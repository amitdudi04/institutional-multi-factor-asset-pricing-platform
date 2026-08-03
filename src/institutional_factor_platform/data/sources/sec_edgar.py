"""Narrow SEC EDGAR company-facts adapter with filing-time preservation."""

import json
from collections.abc import Callable
from datetime import UTC, datetime

from institutional_factor_platform.data.config import SecSettings
from institutional_factor_platform.data.domain import DataSource, RetrievalRequest
from institutional_factor_platform.data.sources.base import HttpTransport, SourceAdapter
from institutional_factor_platform.exceptions import RetrievalError


class SecEdgarAdapter(SourceAdapter[bytes]):
    source = DataSource.SEC_EDGAR

    def __init__(
        self,
        settings: SecSettings,
        transport: HttpTransport,
        now: Callable[[], datetime] = lambda: datetime.now(UTC),
    ) -> None:
        self.settings = settings
        self.transport = transport
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
                            continue
                        filing_date = datetime.strptime(filed, "%Y-%m-%d").date()
                        records.append(
                            {
                                "security_id": request.parameters.get("security_id"),
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
                                "period_end": datetime.strptime(end, "%Y-%m-%d").date(),
                                "filing_date": filing_date,
                                "form": observation.get("form", ""),
                                "accession_number": observation.get("accn"),
                                "frame": observation.get("frame"),
                                "source": self.source.value,
                                "retrieval_timestamp": retrieved,
                                "availability_timestamp": datetime.combine(
                                    filing_date, datetime.min.time(), tzinfo=UTC
                                ),
                                "schema_version": "1.0.0",
                            }
                        )
        if not records:
            raise RetrievalError("SEC company facts contains no usable numeric observations.")
        return tuple(records)


def _date_or_none(value: object) -> object:
    return datetime.strptime(value, "%Y-%m-%d").date() if isinstance(value, str) else None
