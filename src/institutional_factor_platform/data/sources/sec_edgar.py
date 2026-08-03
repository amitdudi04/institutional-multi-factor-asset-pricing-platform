"""Narrow SEC EDGAR company-facts adapter with filing-time preservation."""

import json
from collections.abc import Callable
from datetime import UTC, datetime, time

from institutional_factor_platform.data.config import SecSettings
from institutional_factor_platform.data.domain import DataSource, IssuerId, RetrievalRequest
from institutional_factor_platform.data.security_master import IssuerListingMappingStore
from institutional_factor_platform.data.sources.base import HttpTransport, SourceAdapter
from institutional_factor_platform.exceptions import RetrievalError


class SecEdgarAdapter(SourceAdapter[bytes]):
    source = DataSource.SEC_EDGAR

    def __init__(
        self,
        settings: SecSettings,
        transport: HttpTransport,
        mapping_store: IssuerListingMappingStore | None = None,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.settings = settings
        self.transport = transport
        self.mapping_store = mapping_store
        self.now = now

    def retrieve(self, request: RetrievalRequest) -> bytes:
        cik = request.dataset.zfill(10)
        if len(cik) != 10 or not cik.isdigit():
            raise RetrievalError(f"Invalid SEC CIK: {request.dataset}")
        user_agent = self.settings.require_live_user_agent()
        return self.transport.get(
            f"https://data.sec.gov/api/xbrl/companyfacts/CIK{cik}.json",
            headers={"User-Agent": user_agent, "Accept-Encoding": "gzip, deflate"},
        )

    def standardize(
        self, payload: bytes, request: RetrievalRequest
    ) -> tuple[dict[str, object], ...]:
        try:
            data = json.loads(payload)
        except json.JSONDecodeError as exc:
            raise RetrievalError(f"Invalid SEC JSON: {exc}") from exc
        cik = str(data.get("cik", "")).zfill(10)
        entity = data.get("entityName")
        facts = data.get("facts")
        if not cik.isdigit() or not entity or not isinstance(facts, dict):
            raise RetrievalError("SEC company facts lacks required entity metadata.")
        retrieved = self.now()
        issuer_id = IssuerId.from_cik(cik)
        if request.parameters.get("security_id") is not None:
            raise RetrievalError(
                "SEC caller-supplied listing IDs are prohibited; use persisted issuer mapping."
            )
        records: list[dict[str, object]] = []
        for taxonomy, concepts in facts.items():
            if not isinstance(concepts, dict):
                continue
            for concept, definition in concepts.items():
                if not isinstance(definition, dict):
                    continue
                for unit, observations in definition.get("units", {}).items():
                    for observation in observations:
                        filed = observation.get("filed")
                        end = observation.get("end")
                        if filed is None or end is None or observation.get("val") is None:
                            raise RetrievalError(
                                f"SEC fact {taxonomy}:{concept}:{unit} lacks filed/end/value."
                            )
                        try:
                            filing_date = datetime.strptime(filed, "%Y-%m-%d").date()
                            period_end = datetime.strptime(end, "%Y-%m-%d").date()
                        except (TypeError, ValueError) as exc:
                            raise RetrievalError(
                                f"Malformed SEC fact date for {taxonomy}:{concept}:{unit}: {exc}"
                            ) from exc
                        availability = datetime.combine(filing_date, time.max, tzinfo=UTC)
                        security_id = None
                        if self.mapping_store is not None:
                            try:
                                security_id = self.mapping_store.resolve(
                                    issuer_id, filing_date
                                ).value
                            except Exception as exc:
                                raise RetrievalError(
                                    "SEC issuer-to-listing mapping is unresolved or ambiguous."
                                ) from exc
                        records.append(
                            {
                                "issuer_id": issuer_id.value,
                                "security_id": security_id,
                                "ticker": request.parameters.get("ticker"),
                                "cik": cik,
                                "entity_name": entity,
                                "taxonomy": taxonomy,
                                "concept": concept,
                                "label": definition.get("label"),
                                "description": definition.get("description"),
                                "unit": unit,
                                "value": float(observation["val"]),
                                "fiscal_year": observation.get("fy"),
                                "fiscal_period": observation.get("fp"),
                                "period_start": _date_or_none(observation.get("start")),
                                "period_end": period_end,
                                "filing_date": filing_date,
                                "form": observation.get("form", ""),
                                "accession_number": observation.get("accn"),
                                "frame": observation.get("frame"),
                                "source": self.source.value,
                                "retrieval_timestamp": retrieved,
                                "availability_timestamp": availability,
                                "availability_quality": "INFERRED_DATE_LEVEL",
                                "schema_version": "3.0.0",
                            }
                        )
        if not records:
            raise RetrievalError("SEC company facts contains no usable numeric observations.")
        return tuple(records)


def _date_or_none(value: object) -> object:
    return datetime.strptime(value, "%Y-%m-%d").date() if isinstance(value, str) else None
