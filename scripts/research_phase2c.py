"""Read-only independent verification of Phase 2B, plus one frozen sensitivity.

No production fitting, factor formation, pricing-input or summary helper is used.
Repository authenticators are reused solely to establish persisted authority.
Run: uv run python -X utf8 scripts/research_phase2c.py
"""

import json
import subprocess
from itertools import combinations
from pathlib import Path

import exchange_calendars as xcals
import numpy as np
import pandas as pd
import pyarrow.parquet as pq
import yaml
from phase2c_reference import holm, reference_fit

from institutional_factor_platform.asset_pricing.config import load_asset_pricing_config
from institutional_factor_platform.asset_pricing.models import MODEL_SPECS
from institutional_factor_platform.data.lineage import LifecycleState
from institutional_factor_platform.data.storage import authenticate_dataset_evidence, sha256_file
from institutional_factor_platform.factors.storage import FactorRepository
from institutional_factor_platform.research_outputs.storage import AssetPricingRepository

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "outputs/audit/phase2c"


def load_json(path):
    return json.loads(Path(path).read_text(encoding="utf-8"))


def write_json(path, value):
    Path(path).write_text(json.dumps(value, indent=2, default=str) + "\n", encoding="utf-8")


def authenticate():
    policy = yaml.safe_load((ROOT / "config/research_phase2c.yaml").read_text())
    prior = load_json(ROOT / "outputs/audit/phase2b/PHASE2B_SOURCE_MANIFEST.json")
    archive = Path(prior["source_root"])
    sources = prior["source_artifacts"] + prior["additional_source_artifacts"]
    for source in sources:
        assert sha256_file(Path(source["path"])) == source["sha256"], source["path"]
    factor = FactorRepository(ROOT, ROOT / "data/factor_manifests").authenticate(
        policy["factor_publication"]
    )
    pricing = AssetPricingRepository(ROOT, ROOT / "data/asset_pricing_manifests")
    primary = pricing.authenticate(policy["primary_pricing"])
    supplement = pricing.authenticate(policy["supplementary_pricing"])
    actual = [factor, primary, supplement]
    for record, manifest in zip(prior["new_publication_authority_index"], actual, strict=True):
        assert record["manifest_hash"] == manifest.content_hash()
        assert record["publication_id"] == manifest.publication_id
        assert (
            sha256_file(ROOT / record["publication_file_path"]) == record["publication_file_sha256"]
        )
        assert sha256_file(ROOT / record["manifest_path"]) == record["manifest_file_sha256"]
    assert primary.phase2_manifest_hash == supplement.phase2_manifest_hash == factor.content_hash()
    old_factor = FactorRepository(archive, archive / "data/factor_manifests").authenticate(
        prior["policy"]["historical_factor_publication_id"]
    )
    old_pricing = AssetPricingRepository(
        archive, archive / "data/asset_pricing_manifests"
    ).authenticate(prior["policy"]["historical_pricing_publication_id"])
    assert (
        old_factor.content_hash()
        == prior["old_factor_manifest_hash"]
        == old_pricing.phase2_manifest_hash
    )
    assert old_pricing.content_hash() == prior["old_pricing_manifest_hash"]
    assert factor.artifact_checksum == old_factor.artifact_checksum
    assert factor.parents == old_factor.parents
    parents = {}
    for parent in factor.parents:
        m = authenticate_dataset_evidence(
            parent.dataset_id,
            archive / "data/manifests" / parent.run_id / "dataset.json",
            archive,
            required_state=LifecycleState.FINALIZED,
        )
        assert m.output_checksum == parent.artifact_checksum
        parents[parent.dataset_id.split("_input")[0]] = archive / m.parquet_path
    config = load_asset_pricing_config()
    assert primary.configuration_hash == supplement.configuration_hash == config.canonical_hash()
    for manifest in [primary, supplement]:
        cfg = load_json(
            ROOT / next(a.path for a in manifest.artifacts if a.name == "configuration")
        )
        assert cfg["configuration"] == config.model_dump(mode="json")
        assert set(manifest.model_ids) == set(MODEL_SPECS)
    return policy, prior, archive, factor, pricing, [primary, supplement], parents, config


def reconstruct(factor, parents, config, archive):
    port = pd.read_parquet(ROOT / factor.portfolio_artifact_path)
    for column in ["signal_date", "formation_date", "date"]:
        port[column] = pd.to_datetime(port[column])
    port["asset_id"] = port.factor_id + ":Q" + port["quantile"].astype(str)
    members = pd.read_parquet(
        ROOT / Path(factor.portfolio_artifact_path).parent / "memberships.parquet"
    )
    members["asset_id"] = members.factor_id + ":Q" + members["quantile"].astype(str)
    for column in ["date", "signal_date", "formation_date", "exit_date"]:
        members[column] = pd.to_datetime(members[column])
    market = pd.read_parquet(parents["factor_market"])
    market.date = pd.to_datetime(market.date)
    assert not market.duplicated(["security_id", "date"]).any()
    assert not port.duplicated(["formation_date", "date", "asset_id"]).any()
    sessions = xcals.get_calendar(
        "XNYS", start="2017-01-01", end="2027-01-31"
    ).sessions.tz_localize(None)
    observed = sessions[(sessions >= market.date.min()) & (sessions <= market.date.max())]
    columns = ["market_return", "risk_free"]
    daily = market.groupby("date")[columns].first().sort_index()
    assert daily.index.equals(observed)
    grouped = market.groupby("date")[columns]
    assert ((grouped.max() - grouped.min()).abs() <= 1e-12).all().all()
    assert np.isfinite(market[columns]).all().all() and (market[columns] > -1).all().all()
    # Independently form ranks/weights from every used frozen score, not membership files.
    signals = sorted(port.signal_date.unique())
    scores = pq.read_table(
        ROOT / factor.artifact_path,
        filters=[
            ("date", "in", [d.date() for d in signals]),
            ("factor_id", "in", sorted(port.factor_id.unique())),
        ],
    ).to_pandas()
    scores.date = pd.to_datetime(scores.date)
    caps = scores.loc[scores.factor_id.eq("market_cap"), ["security_id", "date", "raw_value"]]
    caps = caps.rename(columns={"raw_value": "cap"})
    formed = scores.merge(caps, on=["security_id", "date"], validate="many_to_one", sort=False)
    formed = formed.merge(
        market[["security_id", "date", "eligible", "price", "shares_outstanding"]],
        on=["security_id", "date"],
        validate="many_to_one",
        sort=False,
    )
    formed = formed.loc[np.isfinite(formed.score_value) & formed.cap.gt(0) & formed.eligible].copy()
    assert np.allclose(formed.cap, formed.price * formed.shares_outstanding, rtol=1e-12, atol=1e-6)
    cutoff = (
        pd.to_datetime(formed.date, utc=True) + pd.Timedelta(days=1) - pd.Timedelta(microseconds=1)
    )
    assert (pd.to_datetime(formed.available_at, utc=True) <= cutoff).all()
    sizes = formed.groupby(["date", "factor_id"]).security_id.transform("size")
    formed = formed.loc[sizes >= 3].copy()
    formed["quantile"] = np.ceil(
        formed.groupby(["date", "factor_id"]).score_value.rank(method="first", pct=True) * 3
    ).astype(int)
    formed["reference_weight"] = formed.cap / formed.groupby(
        ["date", "factor_id", "quantile"]
    ).cap.transform("sum")
    keys = ["security_id", "date", "factor_id", "quantile"]
    membership_check = formed[[*keys, "reference_weight"]].merge(
        members[[*keys, "weight"]], on=keys, how="outer", validate="one_to_one", indicator=True
    )
    assert membership_check._merge.eq("both").all()
    weight_error = float(
        np.max(np.abs(membership_check.reference_weight - membership_check.weight))
    )
    assert weight_error < 1e-12
    # Genuine frozen endpoints; independent product of all observed quote links as extra check.
    prices = market.set_index(["security_id", "date"]).price
    start = pd.MultiIndex.from_frame(members[["security_id", "formation_date"]])
    end = pd.MultiIndex.from_frame(members[["security_id", "exit_date"]])
    members["reference_return"] = (
        prices.reindex(end).to_numpy() / prices.reindex(start).to_numpy() - 1
    )
    assert np.isfinite(members.reference_return).all()
    assert np.max(np.abs(members.reference_return - members.realized_return)) < 1e-12
    members["contribution"] = members.reference_return * members.weight
    returns = members.groupby(["formation_date", "exit_date", "asset_id"]).contribution.sum()
    returns.index = returns.index.set_names(["formation_date", "date", "asset_id"])
    original = port.set_index(["formation_date", "date", "asset_id"]).value_weighted_return
    return_error = float(np.max(np.abs(returns - original)))
    assert return_error < 1e-12 and len(returns) == len(port) == 11352
    periods = port[["signal_date", "formation_date", "date"]].drop_duplicates()
    holdings = []
    for signal, execution, exit_date in periods.itertuples(index=False, name=None):
        assert signal == sessions[sessions.to_period("M") == signal.to_period("M")][-1]
        assert execution == sessions[sessions.get_loc(signal) + 1]
        next_signal = sessions[sessions.to_period("M") == signal.to_period("M") + 1][-1]
        assert exit_date == sessions[sessions.get_loc(next_signal) + 1] <= market.date.max()
        window = daily.loc[(daily.index > execution) & (daily.index <= exit_date)]
        rm = float(np.prod(1 + window.market_return) - 1)
        rc = float(np.prod(1 + window.risk_free) - 1)
        holdings.append(
            dict(
                formation_date=execution,
                date=exit_date,
                market_excess=rm - rc,
                risk_free_rate=rc,
                expected_sessions=len(window),
            )
        )
    panel = (
        returns.rename("portfolio_return")
        .reset_index()
        .merge(pd.DataFrame(holdings), on=["formation_date", "date"], validate="many_to_one")
    )
    panel["excess_return"] = panel.portfolio_return - panel.risk_free_rate
    wide = returns.unstack("asset_id")
    for alias, characteristic in config.factor_mappings.items():
        spread = (wide[f"{characteristic}:Q3"] - wide[f"{characteristic}:Q1"]).rename(alias)
        panel = panel.merge(
            spread, on=["formation_date", "date"], how="left", validate="many_to_one"
        )
    panel = panel.sort_values(["asset_id", "date"]).reset_index(drop=True)
    assert not panel.duplicated(["asset_id", "date"]).any()
    # Bound mapping check, retaining the earlier exhaustive-source limitation.
    mappings = {
        m["security_id"]: m
        for m in load_json(archive / "outputs/metadata/phase23-hf-security-mappings.json")
    }
    for sid, g in members.groupby("security_id"):
        assert g.signal_date.min() >= pd.Timestamp(mappings[sid]["valid_from"])
        assert g.exit_date.max() <= pd.Timestamp(mappings[sid]["valid_to"])
    return (
        panel,
        members,
        port,
        dict(
            portfolio_return_max_error=return_error,
            weight_max_error=weight_error,
            formation_members=len(members),
            portfolio_rows=len(port),
            calendar_sessions=len(daily),
            sessions_min=min(h["expected_sessions"] for h in holdings),
            sessions_max=max(h["expected_sessions"] for h in holdings),
        ),
    )


def fit_record(fit, asset, model, sample, dates):
    return dict(
        sample_family=sample,
        asset_id=asset,
        model_id=model,
        n=fit["n"],
        k=fit["k"],
        degrees_of_freedom=fit["df"],
        start=str(min(dates)),
        end=str(max(dates)),
        alpha=fit["beta"][0],
        alpha_se=fit["se"][0],
        alpha_t=fit["t"][0],
        alpha_p=fit["p"][0],
        alpha_lower=fit["lower"][0],
        alpha_upper=fit["upper"][0],
        sse=fit["sse"],
        sst=fit["sst"],
        r_squared=fit["r2"],
        adjusted_r_squared=fit["adj"],
        raw_condition=fit["condition"],
        standardized_condition=fit["scaled_condition"],
        max_vif=fit["max_vif"],
        max_regressor_correlation=fit["max_regressor_correlation"],
        residual_mean=fit["residual_mean"],
        normal_equation_scaled=fit["normal_scaled"],
        alpha_mean_identity_error=abs(fit["alpha_mean_identity"] - fit["beta"][0]),
        mean_dependent_excess=fit["mean_y"],
        mean_fitted_factor_contribution=fit["mean_factor_contribution"],
        month_gaps=int(np.sum(np.diff(pd.PeriodIndex(dates, freq="M").asi8) != 1)),
    )


def verify_regressions(panel, repository, manifests, config, policy):
    union = sorted({f for spec in MODEL_SPECS.values() for f in spec.factors})
    primary = panel.loc[np.isfinite(panel[["excess_return", *union]]).all(axis=1)].copy()
    records, differences, dependence = [], [], []
    all_residuals = []
    for family, selected, manifest in zip(
        ["primary", "supplementary"], [primary, panel], manifests, strict=True
    ):
        output = ROOT / "data/asset_pricing" / manifest.publication_id
        published_panel = pd.read_parquet(output / "research_panel.parquet")
        mergekeys = ["asset_id", "formation_date", "date"]
        check_columns = ["excess_return", "risk_free_rate", *union]
        joined = selected[mergekeys + check_columns].merge(
            published_panel[mergekeys + check_columns],
            on=mergekeys,
            suffixes=("_ref", "_pub"),
            how="outer",
            indicator=True,
            validate="one_to_one",
        )
        assert joined._merge.eq("both").all()
        for column in check_columns:
            a, b = joined[column + "_ref"].to_numpy(), joined[column + "_pub"].to_numpy()
            assert np.array_equal(np.isnan(a), np.isnan(b))
            error = float(np.nanmax(np.abs(a - b)))
            assert error < policy["return_absolute_tolerance"]
            differences.append(
                dict(kind="matrix", sample_family=family, metric=column, max_abs_error=error)
            )
        coeff = repository.read_table(manifest.publication_id, "coefficients").to_pandas()
        residuals = repository.read_table(manifest.publication_id, "residuals").to_pandas()
        comparison = repository.read_table(manifest.publication_id, "model_comparison").to_pandas()
        sensitivity = pd.read_parquet(output / "hac_sensitivity.parquet")
        for asset, g in selected.groupby("asset_id", sort=True):
            for model, spec in MODEL_SPECS.items():
                clean = g.loc[np.isfinite(g[["excess_return", *spec.factors]]).all(axis=1)]
                result = reference_fit(clean.excess_return, clean[list(spec.factors)], lag=3)
                record = fit_record(result, asset, model, family, clean.date)
                records.append(record)
                assert record["month_gaps"] == 0
                assert abs(record["residual_mean"]) < 1e-12
                assert record["normal_equation_scaled"] < policy["normal_equation_scaled_tolerance"]
                c = coeff.loc[coeff.asset_id.eq(asset) & coeff.model_id.eq(model)].set_index("term")
                assert set(c.index) == {"const", *spec.factors}
                c = c.loc[["const", *spec.factors]]
                assert c.nobs.eq(len(clean)).all() and c.covariance.eq("HAC").all()
                errors = {}
                for name, col in [
                    ("beta", "estimate"),
                    ("se", "standard_error"),
                    ("t", "t_statistic"),
                    ("p", "p_value"),
                    ("lower", "confidence_lower"),
                    ("upper", "confidence_upper"),
                ]:
                    errors[name] = float(np.max(np.abs(result[name] - c[col])))
                r = residuals.loc[
                    residuals.asset_id.eq(asset) & residuals.model_id.eq(model)
                ].sort_values("date")
                assert pd.to_datetime(r.date).tolist() == clean.date.tolist()
                errors["residual"] = float(np.max(np.abs(result["residual"] - r.residual)))
                errors["fitted"] = float(np.max(np.abs(result["fitted"] - r.fitted_return)))
                errors["dependent"] = float(
                    np.max(np.abs(clean.excess_return.to_numpy() - r.observed_excess_return))
                )
                comp = comparison.loc[
                    comparison.asset_id.eq(asset) & comparison.model_id.eq(model)
                ].iloc[0]
                assert comp.nobs == result["n"]
                errors["r_squared"] = abs(result["r2"] - comp.r_squared)
                errors["adjusted_r_squared"] = abs(result["adj"] - comp.adjusted_r_squared)
                for metric, error in errors.items():
                    differences.append(
                        dict(
                            kind="regression",
                            sample_family=family,
                            asset_id=asset,
                            model_id=model,
                            metric=metric,
                            max_abs_error=error,
                        )
                    )
                    assert error < policy["regression_absolute_tolerance"], (
                        family,
                        asset,
                        model,
                        metric,
                        error,
                    )
                if family == "primary":
                    for lag in policy["hac_lags"]:
                        test = (
                            result
                            if lag == 3
                            else reference_fit(clean.excess_return, clean[list(spec.factors)], lag)
                        )
                        source = sensitivity.loc[
                            sensitivity.asset_id.eq(asset)
                            & sensitivity.model_id.eq(model)
                            & sensitivity.hac_lag.eq(lag)
                        ].iloc[0]
                        for metric, actual in [
                            ("alpha", test["beta"][0]),
                            ("alpha_se", test["se"][0]),
                            ("alpha_p", test["p"][0]),
                        ]:
                            error = abs(source[metric] - actual)
                            differences.append(
                                dict(
                                    kind="hac_sensitivity",
                                    sample_family=family,
                                    asset_id=asset,
                                    model_id=model,
                                    metric=f"{metric}_lag{lag}",
                                    max_abs_error=error,
                                )
                            )
                            assert error < 1e-8
                        dependence.append(
                            dict(
                                kind="hac_intercept",
                                asset_id=asset,
                                model_id=model,
                                lag=lag,
                                alpha=test["beta"][0],
                                standard_error=test["se"][0],
                                p_value=test["p"][0],
                            )
                        )
                    all_residuals.extend(
                        dict(asset_id=asset, model_id=model, date=date, residual=e)
                        for date, e in zip(clean.date, result["residual"], strict=True)
                    )
    records = pd.DataFrame(records)
    for _model, g in records.loc[records.sample_family.eq("primary")].groupby("model_id"):
        records.loc[g.index, "holm_within_model_p"] = holm(g.alpha_p)
    mask = records.sample_family.eq("primary")
    records.loc[mask, "holm_across_615_p"] = holm(records.loc[mask, "alpha_p"])
    assert len(records.loc[mask]) == 615 and records.loc[mask].asset_id.nunique() == 123
    dates = records.loc[mask].groupby("asset_id")[["n", "start", "end"]].nunique()
    assert dates.eq(1).all().all()
    return records, differences, dependence, pd.DataFrame(all_residuals), primary


def summaries(records):
    rows = []
    for (family, model), g in records.groupby(["sample_family", "model_id"]):
        row = dict(
            sample_family=family,
            model_id=model,
            assets=len(g),
            observations=int(g.n.sum()),
            n_min=int(g.n.min()),
            n_max=int(g.n.max()),
            mean_alpha=g.alpha.mean(),
            median_alpha=g.alpha.median(),
            minimum_alpha=g.alpha.min(),
            maximum_alpha=g.alpha.max(),
            sd_alpha=g.alpha.std(ddof=1),
            mean_absolute_alpha=g.alpha.abs().mean(),
            rms_alpha=np.sqrt(np.mean(g.alpha**2)),
            positive_alphas=int(g.alpha.gt(0).sum()),
            negative_alphas=int(g.alpha.lt(0).sum()),
            zero_alphas=int(g.alpha.eq(0).sum()),
            significantly_positive=int((g.alpha.gt(0) & g.alpha_p.lt(0.05)).sum()),
            significantly_negative=int((g.alpha.lt(0) & g.alpha_p.lt(0.05)).sum()),
            not_nominally_significant=int(g.alpha_p.ge(0.05).sum()),
            mean_alpha_se=g.alpha_se.mean(),
            median_alpha_se=g.alpha_se.median(),
            confidence_intervals_containing_zero=int(
                (g.alpha_lower.le(0) & g.alpha_upper.ge(0)).sum()
            ),
            mean_r_squared=g.r_squared.mean(),
            mean_adjusted_r_squared=g.adjusted_r_squared.mean(),
            median_adjusted_r_squared=g.adjusted_r_squared.median(),
            minimum_adjusted_r_squared=g.adjusted_r_squared.min(),
            maximum_adjusted_r_squared=g.adjusted_r_squared.max(),
            q25_adjusted_r_squared=g.adjusted_r_squared.quantile(0.25),
            q75_adjusted_r_squared=g.adjusted_r_squared.quantile(0.75),
            iqr_adjusted_r_squared=g.adjusted_r_squared.quantile(0.75)
            - g.adjusted_r_squared.quantile(0.25),
            sd_adjusted_r_squared=g.adjusted_r_squared.std(ddof=1),
            negative_adjusted_r_squared=int(g.adjusted_r_squared.lt(0).sum()),
            mean_r_squared_minus_adjusted=g.r_squared.mean() - g.adjusted_r_squared.mean(),
            raw_condition_max=g.raw_condition.max(),
            standardized_condition_max=g.standardized_condition.max(),
            max_vif=g.max_vif.max(),
            standardized_condition_gt30=int(g.standardized_condition.gt(30).sum()),
            mean_dependent_excess=g.mean_dependent_excess.mean(),
            mean_fitted_factor_contribution=g.mean_fitted_factor_contribution.mean(),
        )
        if "holm_within_model_p" in g:
            row.update(
                holm_within_model_rejections=int(g.holm_within_model_p.lt(0.05).sum()),
                holm_across_615_rejections=int(g.holm_across_615_p.lt(0.05).sum()),
            )
        rows.append(row)
    return pd.DataFrame(rows)


def dependence_diagnostics(members, port, panel, records, residuals, config):
    rows = []
    wide = port.pivot(
        index=["formation_date", "date"], columns="asset_id", values="value_weighted_return"
    )
    for a, b in combinations(wide.columns, 2):
        pairs = wide[[a, b]].dropna()
        if len(pairs) >= 24 and np.max(np.abs(pairs[a] - pairs[b])) < 1e-12:
            rows.append(
                dict(kind="exact_duplicate_returns", asset_id=a, other_asset=b, n=len(pairs))
            )
    one = panel.drop_duplicates(["formation_date", "date"]).set_index(["formation_date", "date"])
    for a, b in combinations(["market_excess", *config.factor_mappings], 2):
        pairs = one[[a, b]].dropna()
        rows.append(
            dict(
                kind="factor_alias_correlation",
                alias=a,
                other_alias=b,
                n=len(pairs),
                correlation=float(pairs[a].corr(pairs[b])),
                exact_duplicate=bool(np.max(np.abs(pairs[a] - pairs[b])) < 1e-12),
            )
        )
    overlap = []
    for signal, g in members.groupby("signal_date"):
        assets = {a: v for a, v in g.groupby("asset_id")}
        for alias, factor in config.factor_mappings.items():
            low, high = assets.get(f"{factor}:Q1"), assets.get(f"{factor}:Q3")
            if low is None or high is None:
                continue
            union = set(low.security_id) | set(high.security_id)
            for asset, dep in assets.items():
                shared = dep.security_id.isin(union)
                overlap.append(
                    dict(
                        signal=signal,
                        asset_id=asset,
                        alias=alias,
                        shared_fraction=float(shared.mean()),
                        weight_shared=float(dep.loc[shared, "weight"].sum()),
                    )
                )
    overlap = pd.DataFrame(overlap)
    for (asset, alias), g in overlap.groupby(["asset_id", "alias"]):
        rows.append(
            dict(
                kind="constituent_overlap",
                asset_id=asset,
                alias=alias,
                n=len(g),
                mean_shared_fraction=g.shared_fraction.mean(),
                min_shared_fraction=g.shared_fraction.min(),
                max_shared_fraction=g.shared_fraction.max(),
                mean_dependent_weight_shared=g.weight_shared.mean(),
            )
        )
    for model, g in residuals.groupby("model_id"):
        corr = (
            g.pivot(index="date", columns="asset_id", values="residual")
            .corr(min_periods=24)
            .to_numpy()
        )
        upper = corr[np.triu_indices_from(corr, 1)]
        rows.append(
            dict(
                kind="residual_correlation",
                model_id=model,
                n=len(upper),
                mean_correlation=np.nanmean(upper),
                median_correlation=np.nanmedian(upper),
                minimum_correlation=np.nanmin(upper),
                maximum_correlation=np.nanmax(upper),
                pairs_gt095=int((upper > 0.95).sum()),
            )
        )
    primary = records.loc[records.sample_family.eq("primary")]
    for a, b in combinations(MODEL_SPECS, 2):
        x = primary.loc[primary.model_id.eq(a)].set_index("asset_id")
        y = primary.loc[primary.model_id.eq(b)].set_index("asset_id")
        for asset in x.index:
            rows.append(
                dict(
                    kind="paired_model_difference",
                    asset_id=asset,
                    model_id=a,
                    other_model=b,
                    adjusted_r_squared_difference=y.loc[asset, "adjusted_r_squared"]
                    - x.loc[asset, "adjusted_r_squared"],
                    alpha_difference=y.loc[asset, "alpha"] - x.loc[asset, "alpha"],
                )
            )
    corr = wide.corr(min_periods=24).to_numpy()
    upper = corr[np.triu_indices_from(corr, 1)]
    rows.append(
        dict(
            kind="dependent_return_correlation",
            n=len(upper),
            mean_correlation=np.nanmean(upper),
            median_correlation=np.nanmedian(upper),
            minimum_correlation=np.nanmin(upper),
            maximum_correlation=np.nanmax(upper),
            pairs_gt095=int((upper > 0.95).sum()),
        )
    )
    return rows


def sensitivity(members, primary, config):
    """Frozen all-dependent-constituents exclusion, never performance-selected."""
    groups = {(pd.Timestamp(s), a): g for (s, a), g in members.groupby(["signal_date", "asset_id"])}
    cycle_signal = (
        members[["formation_date", "signal_date"]]
        .drop_duplicates()
        .set_index("formation_date")
        .signal_date
    )
    underlying = sorted(set(config.factor_mappings.values()))
    rows, rejected = [], []
    for asset, g in primary.groupby("asset_id", sort=True):
        changed = g.copy()
        for idx, row in g.iterrows():
            signal = pd.Timestamp(cycle_signal.loc[row.formation_date])
            dependent = set(groups[(signal, asset)].security_id)
            spreads = {}
            for factor in underlying:
                values = []
                for quantile in [1, 3]:
                    leg = groups.get((signal, f"{factor}:Q{quantile}"))
                    remaining = None if leg is None else leg.loc[~leg.security_id.isin(dependent)]
                    if remaining is None or remaining.empty:
                        values.append(np.nan)
                    else:
                        weights = remaining.weight / remaining.weight.sum()
                        values.append(float(np.dot(weights, remaining.reference_return)))
                spreads[factor] = values[1] - values[0]
            for alias, factor in config.factor_mappings.items():
                changed.loc[idx, alias] = spreads[factor]
        union = sorted({f for spec in MODEL_SPECS.values() for f in spec.factors})
        keep = np.isfinite(changed[["excess_return", *union]]).all(axis=1)
        changed, baseline = changed.loc[keep], g.loc[keep]
        if len(changed) < 24:
            rejected.append(
                dict(
                    kind="self_exclusion_unestimable",
                    asset_id=asset,
                    n=len(changed),
                    reason="Empty characteristic legs or fewer than 24 common cases; no fallback",
                )
            )
            continue
        fits = []
        try:
            for model, spec in MODEL_SPECS.items():
                for family, frame in [
                    ("self_exclusion", changed),
                    ("sensitivity_matched_baseline", baseline),
                ]:
                    fit = reference_fit(frame.excess_return, frame[list(spec.factors)])
                    fits.append(fit_record(fit, asset, model, family, frame.date))
        except ValueError as exc:
            rejected.append(
                dict(
                    kind="self_exclusion_unestimable",
                    asset_id=asset,
                    n=len(changed),
                    reason=str(exc),
                )
            )
            continue
        rows.extend(fits)
    return pd.DataFrame(rows), rejected


def main():
    OUT.mkdir(parents=True, exist_ok=True)
    policy, prior, archive, factor, repository, manifests, parents, config = authenticate()
    print("All source/publication authorities PASS", flush=True)
    panel, members, portfolios, construction = reconstruct(factor, parents, config, archive)
    print("Independent membership/return/calendar reconstruction PASS", flush=True)
    records, differences, depend, residuals, primary = verify_regressions(
        panel, repository, manifests, config, policy
    )
    print("All primary and supplementary regression comparisons PASS", flush=True)
    depend += dependence_diagnostics(members, portfolios, panel, records, residuals, config)
    extra, rejected = sensitivity(members, primary, config)
    depend += rejected
    all_records = pd.concat([records, extra], ignore_index=True)
    model_summary = summaries(all_records)
    baseline = pd.read_csv(ROOT / "outputs/audit/phase2b/PHASE2B_MODEL_COMPARISON.csv")
    for _, row in model_summary.loc[
        model_summary.sample_family.isin(["primary", "supplementary"])
    ].iterrows():
        family = (
            "primary_matched" if row.sample_family == "primary" else "supplementary_model_specific"
        )
        old = baseline.loc[baseline["sample"].eq(family) & baseline.model_id.eq(row.model_id)].iloc[
            0
        ]
        for current, archived in [
            ("mean_alpha", "mean_alpha"),
            ("mean_absolute_alpha", "mean_absolute_alpha"),
            ("rms_alpha", "rms_alpha"),
            ("mean_adjusted_r_squared", "mean_adjusted_r_squared"),
            ("mean_alpha_se", "mean_hac_alpha_se"),
        ]:
            error = abs(row[current] - old[archived])
            differences.append(
                dict(
                    kind="model_summary",
                    sample_family=row.sample_family,
                    model_id=row.model_id,
                    metric=current,
                    max_abs_error=error,
                )
            )
            assert error < 1e-12
        assert row.significantly_positive + row.significantly_negative == old.nominal_significant
    all_records.to_csv(OUT / "PHASE2C_PORTFOLIO_LEVEL_CHECKS.csv", index=False)
    model_summary.to_csv(OUT / "PHASE2C_MODEL_LEVEL_SUMMARY.csv", index=False)
    pd.DataFrame(differences).to_csv(OUT / "PHASE2C_NUMERICAL_DIFFERENCES.csv", index=False)
    pd.DataFrame(depend).to_csv(OUT / "PHASE2C_DEPENDENCE_AND_CONDITIONING.csv", index=False)
    # Preserve exact source inventories, private paths and authority rather than copying data.
    source = dict(
        base_commit=policy["base_commit"],
        verification_commit=subprocess.check_output(
            ["git", "rev-parse", "HEAD"], cwd=ROOT, text=True
        ).strip(),
        policy=policy,
        prior_source_manifest_sha256=sha256_file(
            ROOT / "outputs/audit/phase2b/PHASE2B_SOURCE_MANIFEST.json"
        ),
        original_source_artifacts=prior["source_artifacts"],
        additional_source_artifacts=prior["additional_source_artifacts"],
        publications=prior["new_publication_authority_index"],
        parents=[p.model_dump(mode="json") for p in factor.parents],
        construction_checks=construction,
        primary_regressions=615,
        supplementary_regressions=615,
        sensitivity_assets=int(extra.asset_id.nunique()),
        sensitivity_rejected_assets=len(rejected),
        production_changes=(
            "None; values unchanged; sensitivity is a diagnostic, not a new official publication"
        ),
        status="PHASE2C_VERIFIED_WITH_ECONOMIC_LIMITATIONS",
    )
    authenticate()
    write_json(OUT / "PHASE2C_SOURCE_MANIFEST.json", source)
    print(
        "Sensitivity complete,",
        source["sensitivity_assets"],
        "assets retained; all final hashes PASS",
        flush=True,
    )


if __name__ == "__main__":
    main()
