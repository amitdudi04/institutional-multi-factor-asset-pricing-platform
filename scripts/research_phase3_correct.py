"""Controlled propagation of demonstrated Phase 3 defects; no new data or design.

Source authority is established once by research_phase3_sources.py. Cached column
projections avoid repeatedly loading 34 million unchanged raw score rows.
"""

import json
import subprocess
from pathlib import Path

import numpy as np
import pandas as pd
import pyarrow.parquet as pq

from institutional_factor_platform.backtest.costs import TransactionCostModel
from institutional_factor_platform.backtest.engine import run_backtest
from institutional_factor_platform.factors.storage import FactorManifest
from institutional_factor_platform.ml.config import MachineLearningConfig
from institutional_factor_platform.ml.contracts import TargetSpecification
from institutional_factor_platform.ml.service import MLResearchService
from institutional_factor_platform.performance.metrics import performance_summary
from institutional_factor_platform.portfolio.config import PortfolioConfig
from institutional_factor_platform.portfolio.service import (
    PortfolioResearchService,
    _publication_id,
    _return_matrix,
    _risk_free_series,
)
from institutional_factor_platform.research_outputs.portfolio_storage import PortfolioManifest
from institutional_factor_platform.research_outputs.storage import AssetPricingManifest

ROOT = Path(__file__).resolve().parents[1]
WORK = ROOT.parent / "phase3"
GATE = json.loads((WORK / "source_gate.json").read_text(encoding="utf-8"))
ARCHIVE = Path(GATE["archive"])


def write(path, value):
    path.write_bytes((json.dumps(value, indent=2, default=str) + "\n").encode())


def document(manifest, name):
    artifact = next(a for a in manifest["artifacts"] if a["name"] == name)
    return json.loads((ARCHIVE / artifact["path"]).read_text(encoding="utf-8"))


def assert_unchanged_sources():
    for artifact in GATE["authenticated_files"]:
        stat = Path(artifact["path"]).stat()
        assert (stat.st_size, stat.st_mtime_ns) == (artifact["bytes"], artifact["mtime_ns"]), (
            artifact["path"]
        )


UPSTREAM = {r["publication_id"]: r for r in GATE["upstream"] if "publication_id" in r}
MARKET_ID = "factor_market_input-89848f8e3c34d53d0432f6e0"
MARKET_PATH = ARCHIVE / f"data/processed/factor_market_input/{MARKET_ID}/data.parquet"


class Factors:
    def __init__(self):
        self.tables = {}

    def authenticate(self, publication_id):
        return FactorManifest.model_validate(UPSTREAM[publication_id])

    def read_portfolios(self, publication_id):
        m = self.authenticate(publication_id)
        base = ROOT if publication_id.startswith("factor-4ddee") else ARCHIVE
        key = (publication_id, "portfolios")
        if key not in self.tables:
            self.tables[key] = pq.read_table(base / m.portfolio_artifact_path)
        return self.tables[key]

    def read_table(self, publication_id):
        m = self.authenticate(publication_id)
        base = ROOT if publication_id.startswith("factor-4ddee") else ARCHIVE
        key = (publication_id, "cash")
        if key not in self.tables:
            self.tables[key] = pq.read_table(
                base / m.artifact_path,
                columns=["date", "factor_id", "raw_value"],
                filters=[("factor_id", "=", "risk_free_rate")],
            )
        return self.tables[key]


class Pricing:
    def authenticate(self, publication_id):
        return AssetPricingManifest.model_validate(UPSTREAM[publication_id])


class Portfolios:
    def authenticate(self, publication_id):
        return PortfolioManifest.model_validate(
            next(m for m in GATE["portfolio"] if m["publication_id"] == publication_id)
        )


class Market:
    def __init__(self):
        self.table = pq.read_table(MARKET_PATH)

    def read_table(self, dataset_id):
        assert dataset_id == MARKET_ID
        return self.table


def portfolio_corrections():
    factors, pricing = Factors(), Pricing()
    source_id = "asset-pricing-d60bee7310b34976c80372a0f0f29e21"
    factor_id = "factor-4ddee9ac6fb45cedfd62a2cc68676b58"
    source = factors.read_portfolios(factor_id).to_pandas()
    returns, benchmark = _return_matrix(source)
    cash = _risk_free_series(factors.read_table(factor_id).to_pandas(), returns.index, source)
    rows = []
    methods = [
        "equal_weight",
        "minimum_variance",
        "mean_variance",
        "maximum_sharpe",
        "maximum_diversification",
        "risk_parity",
        "hrp",
        "cvar",
    ]
    for method in methods:
        originals = [m for m in GATE["portfolio"] if m["method"] == method]
        original_base = (
            next(
                m
                for m in originals
                if m["publication_id"] == "portfolio-dfef8d60d8a771e61224f0b314efd86c"
            )
            if method == "equal_weight"
            else next(
                m
                for m in originals
                if document(m, "configuration")["configuration"]["costs"]["spread_bps"] == 10
            )
        )
        cfg = PortfolioConfig.model_validate(
            document(original_base, "configuration")["configuration"]
        )
        service = PortfolioResearchService(cfg, ROOT, factors, pricing)
        corrected = service.compute_and_publish(source_id, method)
        print("Portfolio BASE", method, corrected.publication_id, flush=True)
        rows.append(
            dict(
                method=method,
                scenario="BASE",
                original_id=original_base["publication_id"],
                corrected=corrected.model_dump(mode="json"),
            )
        )
        # No cost-dependent feasible set/objective is active. Drift is gross-return
        # based, hence each cost scenario uses exactly the same optimized weights.
        assert (
            cfg.constraints.transaction_cost_limit is None
            and cfg.constraints.turnover_limit is None
        )
        allocations = pd.read_parquet(
            ROOT / next(a.path for a in corrected.artifacts if a.name == "allocations")
        )
        weights = allocations.pivot(index="date", columns="asset_id", values="weight").reindex(
            columns=returns.columns
        )
        diagnostics = pd.read_parquet(
            ROOT / next(a.path for a in corrected.artifacts if a.name == "optimization_diagnostics")
        )
        for scenario, spread in [("LOW", 4.0), ("HIGH", 20.0)]:
            old = next(
                m
                for m in originals
                if document(m, "configuration")["configuration"]["costs"]["spread_bps"] == spread
            )
            config = PortfolioConfig.model_validate(document(old, "configuration")["configuration"])
            costs = TransactionCostModel(*config.costs.require_explicit())
            targets = iter(weights.to_numpy())

            def allocator(history, previous, targets=targets):
                return next(targets)

            result = run_backtest(
                returns, benchmark, allocator, costs, window=config.estimation_window
            )
            summary = performance_summary(
                result.returns,
                risk_free=result.returns.date.map(cash),
                annualization=config.annualization_periods,
            )
            commit = subprocess.check_output(
                ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
            ).strip()
            fm, pm = factors.authenticate(factor_id), pricing.authenticate(source_id)
            pid = _publication_id(
                fm.content_hash(), pm.content_hash(), config.canonical_hash(), commit, method, ()
            )
            svc = PortfolioResearchService(config, ROOT, factors, pricing)
            publication = svc._publish(
                pid,
                factor_id,
                fm.content_hash(),
                source_id,
                pm.content_hash(),
                method,
                result.allocations,
                result.transactions,
                result.returns,
                diagnostics,
                summary,
                {
                    "scenarios": [],
                    "status": "NOT_REQUESTED",
                    "exposure_source_publication_id": factor_id,
                },
                commit,
            )
            rows.append(
                dict(
                    method=method,
                    scenario=scenario,
                    original_id=old["publication_id"],
                    corrected=publication.model_dump(mode="json"),
                )
            )
        write(WORK / "corrected_portfolios.json", rows)
    return rows


def corrected_ml_dataset(market):
    original = next(m for m in GATE["ml"] if m["family"] == "linear")
    by = {a["name"]: a for a in original["artifacts"]}
    features = (
        pd.read_parquet(ARCHIVE / by["feature_matrix"]["path"])
        .drop(columns="fold")
        .drop_duplicates()
    )
    source = market.table.to_pandas()
    source.date = pd.to_datetime(source.date, utc=True)
    calendar = pd.DatetimeIndex(sorted(source.date.unique()))
    month_ends = (
        pd.Series(calendar, index=calendar).groupby(calendar.tz_localize(None).to_period("M")).max()
    )
    common = features.loc[features.formation_date.isin(month_ends)].copy()
    histories = {
        sid: g.sort_values("date").reset_index(drop=True)
        for sid, g in source.groupby("security_id")
    }
    targets = []
    for sid, g in common.groupby("security_id"):
        hist = histories[sid]
        local = {d: i for i, d in enumerate(hist.date)}
        values = hist["return"].to_numpy(float)
        benchmarks = hist.benchmark_return.to_numpy(float)
        for decision in g.formation_date:
            start = local[decision]
            expected = calendar.get_loc(decision) + 21
            if (
                expected >= len(calendar)
                or start + 21 >= len(hist)
                or hist.date.iloc[start + 21] != calendar[expected]
            ):
                continue
            v = values[start + 1 : start + 22]
            b = benchmarks[start + 1 : start + 22]
            assert np.isfinite(v).all() and len(v) == 21
            targets.append(
                dict(
                    security_id=sid,
                    formation_date=decision,
                    target=float(np.prod(1 + v) - np.prod(1 + b)),
                    target_start=hist.date.iloc[start + 1],
                    target_end=hist.date.iloc[start + 21],
                    target_available_at=hist.available_at.iloc[start + 21],
                )
            )
    dataset = common.merge(
        pd.DataFrame(targets), on=["security_id", "formation_date"], validate="one_to_one"
    )
    # Original raw score values are reused, not recalculated or replaced.
    fid = original["phase2_publication_id"]
    raw = pq.read_table(
        ARCHIVE / UPSTREAM[fid]["artifact_path"],
        columns=["security_id", "date", "factor_id", "score_value", "available_at"],
        filters=[
            ("factor_id", "in", ["book_to_market", "momentum_12_1m"]),
            ("date", "in", [pd.Timestamp(d).date() for d in dataset.formation_date.unique()]),
        ],
    ).to_pandas()
    raw["formation_date"] = pd.to_datetime(raw.date, utc=True)
    raw_values = raw.pivot(
        index=["security_id", "formation_date"], columns="factor_id", values="score_value"
    )
    joined = dataset.set_index(["security_id", "formation_date"])
    for f in ["book_to_market", "momentum_12_1m"]:
        assert np.allclose(joined[f], raw_values.reindex(joined.index)[f], atol=1e-12, rtol=0)
    availability = raw.groupby(["security_id", "formation_date"]).available_at.max()
    dataset["feature_available_at"] = availability.reindex(joined.index).to_numpy()
    dataset["decision_time"] = (
        dataset.formation_date + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    )
    dataset["feature_coverage"] = 1.0
    assert (pd.to_datetime(dataset.feature_available_at, utc=True) <= dataset.decision_time).all()
    dataset = dataset.sort_values(["formation_date", "security_id"]).reset_index(drop=True)
    card = document(original, "model_card")
    spec = TargetSpecification.model_validate(card["target"])
    assert spec.content_hash() == original["target_hash"]
    metadata = dict(
        phase2_publication_id=fid,
        phase2_manifest_hash=original["phase2_manifest_hash"],
        phase3_publication_id=original["phase3_publication_id"],
        phase3_manifest_hash=original["phase3_manifest_hash"],
        feature_schema_hash=original["feature_schema_hash"],
        target_hash=spec.content_hash(),
        target_specification=spec,
        target_source_dataset_id=MARKET_ID,
        target_source_artifact_checksum="19e7c9bc3cad776bde6de94de6322045c92e5673421c35bd5573c9e411d3e410",
        target_source_unit="decimal_return",
        feature_report={"monthly_rows": len(dataset)},
        git_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
    )
    dataset.to_parquet(WORK / "corrected_ml_dataset.parquet", index=False)
    write(
        WORK / "ml_dataset_changes.json",
        dict(
            original_rows=len(features),
            original_distinct_dates=int(features.formation_date.nunique()),
            original_calendar_months=int(
                features.formation_date.dt.tz_localize(None).dt.to_period("M").nunique()
            ),
            common_month_end_rows=len(common),
            corrected_rows=len(dataset),
            corrected_dates=int(dataset.formation_date.nunique()),
            dropped_off_month_end=features.loc[~features.formation_date.isin(month_ends)]
            .astype(str)
            .to_dict("records"),
            incomplete_targets=common.merge(
                dataset[["security_id", "formation_date"]],
                on=["security_id", "formation_date"],
                how="left",
                indicator=True,
            )
            .loc[lambda x: x._merge.eq("left_only")]
            .astype(str)
            .to_dict("records"),
        ),
    )
    return dataset, metadata


class CachedML(MLResearchService):
    def build_authenticated_dataset(self, phase3_publication_id):
        assert phase3_publication_id == self.cached_metadata["phase3_publication_id"]
        return self.cached_dataset.copy(), self.cached_metadata.copy()


def ml_corrections():
    # The historical portfolio is used only for its authenticated fee configuration.
    # Mirror those exact small metadata bytes for the service's root-relative lookup;
    # the source authority and all empirical data remain in the original archive.
    parent = next(
        m
        for m in GATE["portfolio"]
        if m["publication_id"] == "portfolio-dfef8d60d8a771e61224f0b314efd86c"
    )
    config_artifact = next(a for a in parent["artifacts"] if a["name"] == "configuration")
    target = ROOT / config_artifact["path"]
    content = (ARCHIVE / config_artifact["path"]).read_bytes()
    if target.exists():
        assert target.read_bytes() == content
    else:
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_bytes(content)
    market = Market()
    dataset, metadata = corrected_ml_dataset(market)
    print(
        "Corrected ML input",
        len(dataset),
        "rows,",
        dataset.formation_date.nunique(),
        "monthly dates",
        flush=True,
    )
    rows = []
    for family in [
        "zero",
        "historical_mean",
        "factor_composite",
        "linear",
        "ridge",
        "elastic_net",
        "random_forest",
        "xgboost",
    ]:
        original = next(m for m in GATE["ml"] if m["family"] == family)
        config = MachineLearningConfig.model_validate(document(original, "configuration"))
        service = CachedML(config, ROOT, Factors(), Pricing(), market, Portfolios())
        service.cached_dataset = dataset
        service.cached_metadata = metadata
        manifest = service.train_evaluate_publish(metadata["phase3_publication_id"], family)
        rows.append(
            dict(
                family=family,
                original_id=original["publication_id"],
                corrected=manifest.model_dump(mode="json"),
            )
        )
        write(WORK / "corrected_ml.json", rows)
        print("Corrected ML", family, manifest.publication_id, flush=True)
    return rows


if __name__ == "__main__":
    import sys

    assert_unchanged_sources()
    if "ml" in sys.argv:
        ml_corrections()
    else:
        portfolio_corrections()
