"""Authenticated Phase 2B empirical publication command (no network ingestion).

Run from a clean source checkout: uv run python scripts/research_phase2b.py.
The historical archive is read-only. New artifacts use configured data roots.
This experiment reuses frozen scores, not a claim of independently proved PIT
fundamentals or dividend-total returns. Private holdings are not Git deliverables.
"""

import hashlib
import json
import shutil
import subprocess
from datetime import UTC, datetime
from pathlib import Path

import exchange_calendars as xcals
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from scipy import stats

from institutional_factor_platform.asset_pricing.config import load_asset_pricing_config
from institutional_factor_platform.asset_pricing.inputs import build_research_panel
from institutional_factor_platform.asset_pricing.models import MODEL_SPECS
from institutional_factor_platform.asset_pricing.service import AssetPricingResearchService
from institutional_factor_platform.data.evidence import atomic_write_json, canonical_json_bytes
from institutional_factor_platform.data.lineage import LifecycleState
from institutional_factor_platform.data.storage import authenticate_dataset_evidence, sha256_file
from institutional_factor_platform.diagnostics.regression import regression_diagnostics
from institutional_factor_platform.factors.holding import (
    endpoint_chain,
    form_quantiles,
    matched_sample,
    monthly_cycles,
    validate_session_series,
)
from institutional_factor_platform.factors.portfolio import NON_PORTFOLIO_FACTORS
from institutional_factor_platform.factors.storage import (
    FactorPublication,
    FactorRepository,
    schema_fingerprint,
)
from institutional_factor_platform.regression.engine import fit_regression
from institutional_factor_platform.research_outputs.storage import AssetPricingRepository

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/audit/phase2b"


def digest(value):
    return hashlib.sha256(canonical_json_bytes(value)).hexdigest()


def put(path, value):
    atomic_write_json(path, value)
    return str(path.relative_to(ROOT)).replace("\\", "/"), sha256_file(path)


def bound(path):
    return dict(
        path=path.relative_to(ROOT).as_posix(), sha256=sha256_file(path), bytes=path.stat().st_size
    )


def authenticate():
    policy = yaml.safe_load((ROOT / "config/research_phase2b.yaml").read_text())
    archive = Path(policy["archive_root"])
    prior = json.loads((ROOT / "outputs/audit/phase2/PHASE2_SOURCE_MANIFEST.json").read_text())
    for r in prior["source_artifacts"]:
        if sha256_file(Path(r["path"])) != r["sha256"]:
            raise ValueError(f"Historical evidence changed: {r['path']}")
    old = FactorRepository(archive, archive / "data/factor_manifests").authenticate(
        policy["historical_factor_publication_id"]
    )
    pricing = AssetPricingRepository(
        archive, archive / "data/asset_pricing_manifests"
    ).authenticate(policy["historical_pricing_publication_id"])
    assert old.content_hash() == policy["historical_factor_manifest_hash"]
    assert pricing.content_hash() == policy["historical_pricing_manifest_hash"]
    assert pricing.phase2_manifest_hash == old.content_hash()
    parents = {}
    for parent in old.parents:
        m = authenticate_dataset_evidence(
            parent.dataset_id,
            archive / "data/manifests" / parent.run_id / "dataset.json",
            archive,
            required_state=LifecycleState.FINALIZED,
        )
        assert m.output_checksum == parent.artifact_checksum
        parents[parent.dataset_id.split("_input")[0]] = archive / m.parquet_path
    return policy, archive, prior, old, pricing, parents


def build_factors(policy, archive, old, parents):
    market = pd.read_parquet(parents["factor_market"]).rename(
        columns={"risk_free": "risk_free_rate"}
    )
    market["date"] = pd.to_datetime(market["date"])
    calendar = xcals.get_calendar("XNYS", start="2017-01-01", end="2027-01-31")
    sessions = calendar.sessions.tz_localize(None)
    observed = sessions[(sessions >= market.date.min()) & (sessions <= market.date.max())]
    daily = validate_session_series(market, observed)
    cycles = [
        (s, x, e)
        for s, x, e in monthly_cycles(sessions)
        if s >= market.date.min() and e <= market.date.max()
    ]
    dates = [s.date() for s, _, _ in cycles]
    fp = archive / old.artifact_path
    scores = pq.read_table(fp, filters=[("date", "in", dates)]).to_pandas()
    scores["date"] = pd.to_datetime(scores.date)
    scores = scores.loc[~scores.factor_id.isin(NON_PORTFOLIO_FACTORS)].copy()
    caps = pq.read_table(
        fp,
        columns=["security_id", "date", "raw_value"],
        filters=[("date", "in", dates), ("factor_id", "=", "market_cap")],
    ).to_pandas()
    caps["date"] = pd.to_datetime(caps.date)
    caps = caps.rename(columns={"raw_value": "market_cap"})
    scores = scores.merge(caps, on=["security_id", "date"], validate="many_to_one", sort=False)
    scores = scores.merge(
        market[["security_id", "date", "eligible"]],
        on=["security_id", "date"],
        validate="many_to_one",
        sort=False,
    )
    available = pd.to_datetime(scores.available_at, utc=True)
    cutoff = (
        pd.to_datetime(scores.date, utc=True) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    )
    assert (available <= cutoff).all(), "Used score exceeds declared signal cutoff"
    histories = {sid: g for sid, g in market.groupby("security_id", sort=False)}
    portfolios, members, groups = [], [], []
    for signal, start, end in cycles:
        formed = form_quantiles(scores.loc[scores.date.eq(signal)])
        formed["signal_date"] = signal
        window = observed[(observed >= start) & (observed <= end)]
        security = {}
        for sid in formed.security_id.unique():
            value, reason, count = endpoint_chain(histories[sid], start, end, observed)
            security[sid] = (value, reason, count)
        hold = daily.loc[(daily.index > start) & (daily.index <= end)]
        assert len(hold) == len(window) - 1
        benchmark = float(np.prod(1 + hold.market_return) - 1)
        for (factor, quantile), g in formed.groupby(["factor_id", "quantile"], sort=True):
            failures = [sid for sid in g.security_id if security[sid][0] is None]
            record = dict(
                signal_date=signal,
                formation_date=start,
                date=end,
                factor_id=factor,
                quantile=int(quantile),
                security_count=len(g),
                expected_holding_sessions=len(hold),
                status="INCOMPLETE_UNRECOVERABLE" if failures else "COMPLETE_VALID",
                failed_security_ids=json.dumps(failures),
                reasons=json.dumps(sorted({security[sid][1] for sid in failures})),
            )
            groups.append(record)
            g = g.copy()
            g["formation_date"] = start
            g["exit_date"] = end
            g["realized_return"] = g.security_id.map({sid: v[0] for sid, v in security.items()})
            g["chain_status"] = g.security_id.map({sid: v[1] for sid, v in security.items()})
            g["observed_quotes"] = g.security_id.map({sid: v[2] for sid, v in security.items()})
            g["group_admitted"] = not failures
            members.append(g)
            if failures:
                continue
            value = float(np.dot(g.weight, g.realized_return))
            assert abs(g.weight.sum() - 1) < 1e-12 and (g.weight > 0).all()
            portfolios.append(
                {
                    **record,
                    "value_weighted_return": value,
                    "benchmark_return": benchmark,
                    "active_return": value - benchmark,
                    "available_at": end.tz_localize("UTC")
                    + pd.Timedelta(days=1)
                    - pd.Timedelta(microseconds=1),
                    "factor_version": old.factor_version,
                }
            )
    return (
        market,
        daily,
        pd.DataFrame(portfolios),
        pd.concat(members, ignore_index=True),
        pd.DataFrame(groups),
    )


def publish_factor(policy, archive, old, portfolios, members, groups, commit):
    snapshot = {
        "frozen_factor_configuration": json.loads(
            (archive / old.configuration_snapshot_path).read_text()
        ),
        "correction_policy": policy,
    }
    cfg = digest(snapshot)
    fid = "factor-" + digest(dict(parent=old.content_hash(), configuration=cfg, source=commit))[:32]
    output = ROOT / policy["factor_output_root"] / fid
    meta = ROOT / policy["factor_manifest_root"] / fid
    output.mkdir(parents=True, exist_ok=False)
    meta.mkdir(parents=True, exist_ok=False)
    artifact = output / "factors.parquet"
    shutil.copyfile(archive / old.artifact_path, artifact)
    assert sha256_file(artifact) == old.artifact_checksum
    pp = output / "factor-portfolios.parquet"
    portfolios.to_parquet(pp, index=False)
    for name, frame in [("memberships", members), ("admissibility", groups)]:
        frame.to_parquet(output / f"{name}.parquet", index=False)
    config_path, config_sha = put(meta / "configuration.json", snapshot)
    vp, vs = put(
        meta / "validation.json",
        dict(
            publication_id=fid,
            status="PASS_WITH_WARNINGS",
            row_count=old.row_count,
            portfolio_rows=len(portfolios),
            rejected_groups=int(groups.status.ne("COMPLETE_VALID").sum()),
            warnings=[
                policy["price_return_label"],
                "Representative PIT evidence is not exhaustive validation.",
            ],
        ),
    )
    dp, ds = put(
        meta / "diagnostics.json",
        dict(
            publication_id=fid,
            methodology_id=policy["methodology_id"],
            parent_publication_id=old.publication_id,
            parent_manifest_hash=old.content_hash(),
            raw_scores="Byte-identical frozen scores; no re-estimated definitions",
            bound_supplementary_artifacts=[
                bound(output / "memberships.parquet"),
                bound(output / "admissibility.parquet"),
            ],
            policy=policy,
        ),
    )
    lineage = json.loads((archive / old.lineage_path).read_text())
    lineage.update(
        publication_id=fid,
        portfolio_artifact_checksum=sha256_file(pp),
        transformation=policy["methodology_id"],
        git_commit=commit,
        configuration_hash=cfg,
        historical_parent_publication_id=old.publication_id,
        historical_parent_manifest_hash=old.content_hash(),
    )
    lp, ls = put(meta / "lineage.json", lineage)
    manifest = old.model_copy(
        update=dict(
            publication_id=fid,
            created_at=datetime.now(UTC),
            artifact_path=artifact.relative_to(ROOT).as_posix(),
            portfolio_artifact_path=pp.relative_to(ROOT).as_posix(),
            portfolio_artifact_checksum=sha256_file(pp),
            portfolio_artifact_byte_size=pp.stat().st_size,
            portfolio_schema_fingerprint=schema_fingerprint(pq.read_schema(pp)),
            portfolio_row_count=len(portfolios),
            configuration_hash=cfg,
            configuration_snapshot_path=config_path,
            configuration_snapshot_checksum=config_sha,
            validation_report_path=vp,
            validation_report_checksum=vs,
            validation_status="PASS_WITH_WARNINGS",
            diagnostics_path=dp,
            diagnostics_checksum=ds,
            lineage_path=lp,
            lineage_checksum=ls,
            git_commit=commit,
        )
    )
    mp, _ = put(meta / "factor-manifest.json", manifest.model_dump(mode="json"))
    pub = FactorPublication(
        schema_version="1.0.0",
        publication_id=fid,
        manifest_path=mp,
        manifest_hash=manifest.content_hash(),
        artifact_checksum=manifest.artifact_checksum,
        git_commit=commit,
        configuration_hash=cfg,
    )
    put(meta / "factor-publication.json", pub.model_dump(mode="json"))
    FactorRepository(ROOT, ROOT / policy["factor_manifest_root"]).authenticate(fid)
    return manifest


def reference_fit(frame, factors, lag):
    """Independent NumPy Bartlett sandwich, not statsmodels or production helpers."""
    clean = frame[["excess_return", *factors]].dropna()
    y = clean.excess_return.to_numpy()
    x = np.column_stack([np.ones(len(y)), clean[list(factors)].to_numpy()])
    n, k = x.shape
    beta = np.linalg.lstsq(x, y, rcond=None)[0]
    residual = y - x @ beta
    bread = np.linalg.inv(x.T @ x)
    scores = x * residual[:, None]
    meat = scores.T @ scores
    for j in range(1, lag + 1):
        gamma = scores[j:].T @ scores[:-j]
        meat += (1 - j / (lag + 1)) * (gamma + gamma.T)
    se = np.sqrt(np.diag(bread @ meat @ bread * n / (n - k)))
    p = 2 * stats.t.sf(np.abs(beta / se), n - k)
    r2 = 1 - residual @ residual / np.sum((y - y.mean()) ** 2)
    return beta, se, p, residual, 1 - (1 - r2) * (n - 1) / (n - k)


def pricing(panel, factor_manifest, policy, commit, mode):
    config = load_asset_pricing_config()
    all_factors = tuple(sorted({f for s in MODEL_SPECS.values() for f in s.factors}))
    selected = matched_sample(panel, all_factors) if mode == "primary_matched" else panel
    aid = (
        "asset-pricing-"
        + digest(
            dict(
                parent=factor_manifest.content_hash(),
                configuration=config.canonical_hash(),
                sample=mode,
                source=commit,
            )
        )[:32]
    )
    coefficients, residuals, comparisons, influences, fits, diffs, sensitivity, omitted = (
        [] for _ in range(8)
    )
    accepted_assets = []
    for asset_id, asset in selected.groupby("asset_id", sort=True):
        results = {}
        for model, spec in MODEL_SPECS.items():
            try:
                results[model] = fit_regression(
                    asset,
                    "excess_return",
                    spec.factors,
                    model_id=model,
                    covariance="HAC",
                    hac_lags=3,
                    minimum_observations=24,
                )
            except Exception as exc:
                omitted.append(dict(asset_id=asset_id, model_id=model, reason=str(exc)))
        if mode == "primary_matched" and len(results) != 5:
            continue
        accepted_assets.append(asset_id)
        for model, result in results.items():
            spec = MODEL_SPECS[model]
            clean = asset.loc[result.residuals.index]
            beta, se, p, e, adj = reference_fit(clean, spec.factors, 3)
            c = result.coefficients
            differences = dict(
                coefficient=float(np.max(np.abs(beta - c.estimate))),
                hac_se=float(np.max(np.abs(se - c.standard_error))),
                p_value=float(np.max(np.abs(p - c.p_value))),
                residual=float(np.max(np.abs(e - result.residuals))),
                adjusted_r_squared=abs(adj - result.metrics["adjusted_r_squared"]),
            )
            assert max(differences.values()) < 1e-8, differences
            diffs.append(dict(sample=mode, asset_id=asset_id, model_id=model, **differences))
            coefficients.append(
                c.assign(asset_id=asset_id, model_id=model, nobs=result.nobs, covariance="HAC")
            )
            residuals.append(
                pd.DataFrame(
                    dict(
                        asset_id=asset_id,
                        model_id=model,
                        date=clean.date,
                        observed_excess_return=clean.excess_return,
                        fitted_return=result.fitted,
                        residual=result.residuals,
                    )
                )
            )
            comparisons.append(
                dict(asset_id=asset_id, model_id=model, nobs=result.nobs, **result.metrics)
            )
            _, influence = regression_diagnostics(result, asset, spec.factors)
            influences.append(influence.assign(asset_id=asset_id, model_id=model))
            alpha = c.iloc[0]
            fits.append(
                dict(
                    sample=mode,
                    asset_id=asset_id,
                    model_id=model,
                    n=result.nobs,
                    start=str(clean.date.min()),
                    end=str(clean.date.max()),
                    adjusted_r_squared=adj,
                    alpha=alpha.estimate,
                    alpha_se=alpha.standard_error,
                    alpha_t=alpha.t_statistic,
                    alpha_p=alpha.p_value,
                    dates_hash=digest([str(d) for d in clean.date]),
                    month_gaps=int(
                        pd.PeriodIndex(clean.date, freq="M")
                        .to_series()
                        .diff()
                        .dropna()
                        .map(lambda d: d.n != 1)
                        .sum()
                    ),
                )
            )
            for lag in [0, 3, 6, 12]:
                b, s, pv, _, _ = reference_fit(clean, spec.factors, lag)
                check = fit_regression(
                    clean, "excess_return", spec.factors, hac_lags=lag, minimum_observations=24
                )
                assert np.allclose(s, check.coefficients.standard_error, atol=1e-8, rtol=0)
                assert np.allclose(pv, check.coefficients.p_value, atol=1e-8, rtol=0)
                sensitivity.append(
                    dict(
                        asset_id=asset_id,
                        model_id=model,
                        hac_lag=lag,
                        alpha=float(b[0]),
                        alpha_se=float(s[0]),
                        alpha_p=float(pv[0]),
                    )
                )
    output = ROOT / policy["pricing_output_root"] / aid
    output.mkdir(parents=True, exist_ok=False)
    extras = []
    for name, frame in [
        ("research_panel", selected.loc[selected.asset_id.isin(accepted_assets)]),
        ("fit_samples", pd.DataFrame(fits)),
        ("hac_sensitivity", pd.DataFrame(sensitivity)),
        ("independent_reconciliation", pd.DataFrame(diffs)),
    ]:
        path = output / f"{name}.parquet"
        frame.to_parquet(path, index=False)
        extras.append(bound(path))
    diagnostics = dict(
        publication_id=aid,
        methodology_id=policy["methodology_id"],
        sample_policy=mode,
        bound_supplementary_artifacts=extras,
        omitted=omitted,
        policy=policy,
        rolling_status="Not estimated in this bounded full-sample correction; empty typed artifact",
        qualification=(
            "Frozen adjusted-quote returns; PIT representative only; "
            "dependent test assets; nominal inference"
        ),
    )
    rolling = pd.DataFrame(
        columns=[
            "window_end",
            "window_start",
            "term",
            "estimate",
            "standard_error",
            "t_statistic",
            "p_value",
            "confidence_lower",
            "confidence_upper",
            "asset_id",
            "model_id",
            "window_type",
        ]
    )
    service = AssetPricingResearchService(
        config, ROOT, FactorRepository(ROOT, ROOT / policy["factor_manifest_root"])
    )
    manifest = service._publish(
        aid,
        factor_manifest.publication_id,
        factor_manifest.content_hash(),
        tuple(sorted(MODEL_SPECS)),
        selected.loc[selected.asset_id.isin(accepted_assets)],
        pd.concat(coefficients, ignore_index=True),
        pd.concat(residuals, ignore_index=True),
        pd.DataFrame(comparisons),
        rolling,
        pd.concat(influences, ignore_index=True),
        diagnostics,
        commit,
        MODEL_SPECS,
    )
    return manifest, pd.DataFrame(fits), pd.DataFrame(diffs)


def main():
    if subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True).strip():
        raise ValueError("Publication requires committed clean source")
    commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    OUT.mkdir(parents=True, exist_ok=True)
    policy, archive, prior, old, old_pricing, parents = authenticate()
    print("Source gate PASS", flush=True)
    market, daily, portfolios, members, groups = build_factors(policy, archive, old, parents)
    print(
        "Constructed",
        len(portfolios),
        "retained;",
        len(groups) - len(portfolios),
        "rejected",
        flush=True,
    )
    factor = publish_factor(policy, archive, old, portfolios, members, groups, commit)
    # Use the published artifact, not a separately patched diagnostic table.
    published = pd.read_parquet(ROOT / factor.portfolio_artifact_path)
    common = pq.read_table(
        ROOT / factor.artifact_path,
        filters=[("factor_id", "in", ["market_return", "risk_free_rate", "excess_return"])],
    ).to_pandas()
    panel = build_research_panel(common, published, load_asset_pricing_config().factor_mappings)
    primary, fits, differences = pricing(panel, factor, policy, commit, "primary_matched")
    print("Primary pricing published", primary.publication_id, flush=True)
    secondary, supplement, sd = pricing(
        panel, factor, policy, commit, "supplementary_model_specific"
    )
    pd.concat([differences, sd]).to_csv(OUT / "PHASE2B_PRICING_RECONCILIATION.csv", index=False)
    # Independent constituent price-ratio aggregation, from input panel and stored weights.
    used = members.loc[members.group_admitted].copy()
    quote_index = market.set_index(["security_id", "date"]).price
    start = pd.MultiIndex.from_frame(used[["security_id", "formation_date"]])
    end = pd.MultiIndex.from_frame(used[["security_id", "exit_date"]])
    used["reference_contribution"] = used.weight.to_numpy() * (
        quote_index.reindex(end).to_numpy() / quote_index.reindex(start).to_numpy() - 1
    )
    ref = used.groupby(["signal_date", "factor_id", "quantile"]).reference_contribution.sum()
    check = portfolios.set_index(["signal_date", "factor_id", "quantile"]).value_weighted_return
    assert np.max(np.abs(ref - check)) < 1e-12
    oldp = pd.read_parquet(archive / old.portfolio_artifact_path).rename(
        columns={
            "formation_date": "signal_date",
            "date": "historical_exit",
            "value_weighted_return": "historical_return",
        }
    )
    recon = oldp[
        ["signal_date", "historical_exit", "factor_id", "quantile", "historical_return"]
    ].copy()
    recon["signal_date"] = pd.to_datetime(recon.signal_date)
    recon = recon.merge(
        portfolios[["signal_date", "date", "factor_id", "quantile", "value_weighted_return"]],
        on=["signal_date", "factor_id", "quantile"],
        how="outer",
    )
    recon["difference"] = recon.value_weighted_return - recon.historical_return
    recon["comparison_note"] = (
        "Changed execution/end horizon; matched signal is not a same-interval correction"
    )
    recon.to_csv(OUT / "PHASE2B_FACTOR_RECONCILIATION.csv", index=False)
    summary = []
    prior_families = [
        ("historical_original", "reproduced_regressions.csv"),
        ("phase2_conditional_interval", "interval_corrected_regressions.csv"),
    ]
    # Accepted Phase2 evidence supplies these two unchanged, independently reconciled families.
    for label, filename in prior_families:
        path = ROOT.parent / "phase2" / filename
        frame = pd.read_csv(path).rename(columns={"adj": "adjusted_r_squared", "p": "alpha_p"})
        frame["sample"] = label
        summary.append(frame)
    summary += [fits, supplement]
    allfits = pd.concat(summary, ignore_index=True)
    allfits.to_csv(OUT / "PHASE2B_MODEL_FIT_EVIDENCE.csv", index=False)
    rows = []
    for (sample, model), g in allfits.groupby(["sample", "model_id"]):
        rows.append(
            dict(
                sample=sample,
                model_id=model,
                assets=len(g),
                observations=int(g.n.sum()),
                n_min=int(g.n.min()),
                n_max=int(g.n.max()),
                mean_adjusted_r_squared=float(g.adjusted_r_squared.mean()),
                mean_alpha=float(g.alpha.mean()),
                mean_absolute_alpha=float(g.alpha.abs().mean()),
                rms_alpha=float(np.sqrt(np.mean(g.alpha**2))),
                mean_hac_alpha_se=float(g.alpha_se.mean()),
                nominal_significant=int(g.alpha_p.lt(0.05).sum()),
                nominal_percent=float(g.alpha_p.lt(0.05).mean() * 100),
            )
        )
    pd.DataFrame(rows).to_csv(OUT / "PHASE2B_MODEL_COMPARISON.csv", index=False)
    source = dict(
        source_root=str(archive),
        git_commit=commit,
        policy=policy,
        source_artifacts=prior["source_artifacts"],
        old_factor_manifest_hash=old.content_hash(),
        old_pricing_manifest_hash=old_pricing.content_hash(),
        new_factor=factor.model_dump(mode="json"),
        new_primary_pricing=primary.model_dump(mode="json"),
        new_supplementary_pricing=secondary.model_dump(mode="json"),
        portfolio_count=len(portfolios),
        candidate_groups=len(groups),
        membership_rows=len(members),
        retained_memberships=len(used),
        common_calendar_sessions=len(daily),
        independent_factor_max_error=float(np.max(np.abs(ref - check))),
        terminal_partial_periods="No cycle ending after final observed session admitted",
        primary_missing_assets=sorted(set(panel.asset_id) - set(fits.asset_id)),
        calendar_package_version=xcals.__version__,
    )
    # Reauthenticate outputs, bound extras and every historical source after computation.
    for manifest in [factor, primary, secondary]:
        if manifest is factor:
            FactorRepository(ROOT, ROOT / policy["factor_manifest_root"]).authenticate(
                manifest.publication_id
            )
            diagnostic = json.loads((ROOT / manifest.diagnostics_path).read_text())
        else:
            AssetPricingRepository(ROOT, ROOT / policy["pricing_manifest_root"]).authenticate(
                manifest.publication_id
            )
            path = next(a.path for a in manifest.artifacts if a.name == "diagnostics")
            diagnostic = json.loads((ROOT / path).read_text())
        for a in diagnostic["bound_supplementary_artifacts"]:
            assert sha256_file(ROOT / a["path"]) == a["sha256"]
    authenticate()
    put(OUT / "PHASE2B_SOURCE_MANIFEST.json", source)
    print("All immutable publications and independent numerical comparisons PASS", flush=True)


if __name__ == "__main__":
    main()
