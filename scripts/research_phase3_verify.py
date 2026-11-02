"""Independent accounting, original/corrected portfolio and ML reconciliations."""

import hashlib
import io
import json
from pathlib import Path

import joblib
import numpy as np
import pandas as pd
from research_phase3_correct import ARCHIVE, GATE, MARKET_PATH, ROOT, WORK, assert_unchanged_sources
from scipy.stats import norm, rankdata
from sklearn.covariance import LedoitWolf

from institutional_factor_platform.ml.publication import MLRepository
from institutional_factor_platform.research_outputs.portfolio_storage import PortfolioRepository

OUT = ROOT / "outputs/audit/phase3"


def read(path):
    return json.loads(Path(path).read_bytes())


def artifact(root, manifest, name):
    return root / next(a["path"] for a in manifest["artifacts"] if a["name"] == name)


def table(root, manifest, name):
    return pd.read_parquet(artifact(root, manifest, name))


def cash_returns(market, periods, dates):
    daily = market.groupby("date").risk_free.first()
    periods = periods[["formation_date", "date"]].drop_duplicates().set_index("date")
    result = []
    for date in dates:
        start = pd.Timestamp(periods.loc[date, "formation_date"])
        hold = daily.loc[(daily.index > start) & (daily.index <= date)]
        assert len(hold) > 0
        result.append(float(np.prod(1 + hold.to_numpy()) - 1))
    return np.asarray(result)


def risk_reference(r, rf):
    r = np.asarray(r, float)
    excess = r - rf
    wealth = np.cumprod(1 + r)
    peaks = np.maximum.accumulate(np.r_[1.0, wealth])[1:]
    old_peaks = np.maximum.accumulate(wealth)
    threshold = np.quantile(r, 0.05)
    return dict(
        cumulative_return=float(wealth[-1] - 1),
        wealth=float(wealth[-1]),
        annualized_return=float(wealth[-1] ** (12 / len(r)) - 1),
        volatility=float(np.std(r, ddof=1) * np.sqrt(12)),
        sharpe=float(np.mean(excess) / np.std(excess, ddof=1) * np.sqrt(12)),
        maximum_drawdown=float(np.min(wealth / peaks - 1)),
        old_peak_drawdown=float(np.min(wealth / old_peaks - 1)),
        historical_var_95=max(0.0, float(-threshold)),
        cvar_95=max(0.0, float(-r[r <= threshold].mean())),
        parametric_var_95=max(0.0, float(-(r.mean() + norm.ppf(0.05) * r.std(ddof=1)))),
        tail_observations=int(np.sum(r <= threshold)),
    )


def portfolio_audit(market, old_rows, new_rows):
    old_factor = next(
        m for m in GATE["upstream"] if m.get("publication_id", "").startswith("factor-5a736")
    )
    new_factor = next(
        m for m in GATE["upstream"] if m.get("publication_id", "").startswith("factor-4ddee")
    )
    matrices, intervals = {}, {}
    for family, base, fm in [("old", ARCHIVE, old_factor), ("new", ROOT, new_factor)]:
        f = pd.read_parquet(base / fm["portfolio_artifact_path"])
        f.date = pd.to_datetime(f.date)
        f.formation_date = pd.to_datetime(f.formation_date)
        f["asset_id"] = f.factor_id + ":Q" + f["quantile"].astype(str)
        matrices[family] = (
            f.pivot(index="date", columns="asset_id", values="value_weighted_return")
            .sort_index()
            .dropna()
        )
        intervals[family] = f
    checks, reconciliation, facts = [], [], []
    for row in new_rows:
        method, scenario = row["method"], row["scenario"]
        originals = next(m for m in old_rows if m["publication_id"] == row["original_id"])
        result_metrics = {}
        for family, base, manifest in [
            ("old", ARCHIVE, originals),
            ("new", ROOT, row["corrected"]),
        ]:
            returns = table(base, manifest, "returns")
            returns.date = pd.to_datetime(returns.date)
            allocations = table(base, manifest, "allocations")
            allocations.date = pd.to_datetime(allocations.date)
            trades = table(base, manifest, "transactions")
            trades.date = pd.to_datetime(trades.date)
            cfg = read(artifact(base, manifest, "configuration"))["configuration"]
            costs = cfg["costs"]
            weights = allocations.pivot(
                index="date", columns="asset_id", values="weight"
            ).sort_index()
            matrix = matrices[family].reindex(columns=weights.columns)
            assert len(weights) == len(returns) and np.allclose(weights.sum(axis=1), 1, atol=1e-7)
            assert weights.min().min() >= -1e-7 and weights.max().max() <= 1 + 1e-7
            prev = np.zeros(weights.shape[1])
            nav = 1.0
            all_errors = []
            diagnostics = table(base, manifest, "optimization_diagnostics")
            for i, r in returns.iterrows():
                w = weights.loc[r.date].to_numpy()
                delta = w - prev
                tx = (
                    trades.loc[trades.date.eq(r.date)]
                    .set_index("asset_id")
                    .reindex(weights.columns)
                    .fillna(0)
                )
                trade_error = float(np.max(np.abs(delta - tx.trade_weight.to_numpy())))
                per_asset = {
                    "turnover": np.abs(delta),
                    "commission": np.abs(delta) * costs["commission_bps"] / 1e4,
                    "spread": np.abs(delta) * costs["spread_bps"] / 2e4,
                    "slippage": np.abs(delta) * costs["slippage_bps"] / 1e4,
                    "market_impact": np.zeros(len(w)),
                }
                per_asset["total_cost"] = (
                    per_asset["commission"] + per_asset["spread"] + per_asset["slippage"]
                )
                fee_error = max(
                    float(np.max(np.abs(tx[k].to_numpy() - v))) for k, v in per_asset.items()
                )
                fee = float(per_asset["total_cost"].sum())
                gross = float(np.dot(w, matrix.loc[r.date]))
                net = gross - fee
                nav_before = nav
                nav = nav_before * (1 + net)
                ledger_error = abs(nav - (nav_before * (1 + gross) - nav_before * fee))
                error = max(
                    trade_error,
                    fee_error,
                    abs(gross - r.gross_return),
                    abs(net - r.net_return),
                    abs(fee - r.transaction_cost),
                    ledger_error,
                )
                assert error < 1e-9, (method, scenario, family, r.date, error)
                all_errors.append(error)
                period = (
                    intervals[family].loc[intervals[family].date.eq(r.date)].formation_date.unique()
                )
                assert len(period) == 1
                position = matrix.index.get_loc(r.date)
                history = matrix.iloc[position - cfg["estimation_window"] : position]
                assert len(history) == 36 and history.index.max() <= pd.Timestamp(period[0])
                checks.append(
                    dict(
                        kind="trade_and_nav",
                        method=method,
                        scenario=scenario,
                        publication_id=manifest["publication_id"],
                        source_category="HISTORICAL_ORIGINAL"
                        if family == "old"
                        else "CORRECTED_AUTHENTICATED",
                        date=r.date,
                        formation_date=period[0],
                        training_start=history.index.min(),
                        training_end=history.index.max(),
                        training_periods=len(history),
                        initial_deployment=i == 0,
                        l1_turnover=float(np.abs(delta).sum()),
                        half_l1=float(np.abs(delta).sum() / 2),
                        commission=float(per_asset["commission"].sum()),
                        half_spread=float(per_asset["spread"].sum()),
                        slippage_plus_fixed=float(per_asset["slippage"].sum()),
                        cost=fee,
                        nav_before=nav_before,
                        nav_after=nav,
                        gross=gross,
                        net=net,
                        max_trade_error=trade_error,
                        max_cost_error=fee_error,
                        max_nav_error=ledger_error,
                    )
                )
                if method != "equal_weight":
                    covariance = LedoitWolf().fit(history.to_numpy()).covariance_ * 12
                    mean = history.mean().to_numpy() * 12
                    variance = float(w @ covariance @ w)
                    objective = {
                        "minimum_variance": variance,
                        "mean_variance": variance - float(mean @ w),
                        "maximum_sharpe": -float(mean @ w) / np.sqrt(variance),
                        "maximum_diversification": -float(w @ np.sqrt(np.diag(covariance)))
                        / np.sqrt(variance),
                        "risk_parity": float(
                            np.sum((w * (covariance @ w) / variance - 1 / len(w)) ** 2)
                        ),
                        "hrp": 0.0,
                    }
                    if method == "cvar":
                        losses = -history.to_numpy() @ w
                        objective[method] = float(
                            min(t + np.maximum(losses - t, 0).mean() / 0.05 for t in losses)
                        )
                    diag = diagnostics.iloc[i]
                    diff = max(
                        abs(diag.expected_return - float(mean @ w)),
                        abs(diag.volatility - np.sqrt(variance)),
                        abs(diag.objective_value - objective[method]),
                    )
                    assert diff < 1e-7, (method, family, diff)
                    checks.append(
                        dict(
                            kind="optimization",
                            method=method,
                            scenario=scenario,
                            date=r.date,
                            source_category=family,
                            objective=objective[method],
                            max_error=diff,
                            max_weight=float(w.max()),
                            risk_free_assumption=0.0,
                            min_covariance_eigenvalue=float(np.linalg.eigvalsh(covariance).min()),
                        )
                    )
                prev = w * (1 + matrix.loc[r.date].to_numpy()) / (1 + gross)
            summary = read(artifact(base, manifest, "performance_summary"))
            old_rf = market.groupby("date").risk_free.first().reindex(returns.date).to_numpy()
            cash = cash_returns(market, intervals[family], returns.date)
            reference = risk_reference(returns.net_return, old_rf if family == "old" else cash)
            for metric in [
                "cumulative_return",
                "volatility",
                "sharpe",
                "maximum_drawdown",
                "historical_var_95",
                "cvar_95",
                "parametric_var_95",
            ]:
                assert abs(reference[metric] - summary["risk"][metric]) < 1e-10, (
                    method,
                    family,
                    metric,
                )
            corrected_cash_only = risk_reference(returns.net_return, cash)
            result_metrics[family] = dict(
                **reference,
                fee_sum=float(returns.transaction_cost.sum()),
                fee_wealth_effect=float(
                    np.prod(1 + returns.gross_return) - np.prod(1 + returns.net_return)
                ),
                cash_corrected_sharpe=corrected_cash_only["sharpe"],
                n=len(returns),
                start=str(returns.date.min()),
                end=str(returns.date.max()),
            )
            checks.append(
                dict(
                    kind="risk",
                    method=method,
                    scenario=scenario,
                    source_category=family,
                    publication_id=manifest["publication_id"],
                    **reference,
                    cash_corrected_sharpe=corrected_cash_only["sharpe"],
                    initial_nav_effect=reference["maximum_drawdown"]
                    - reference["old_peak_drawdown"],
                )
            )
        a, b = result_metrics["old"], result_metrics["new"]
        reconciliation.append(
            dict(
                method=method,
                scenario=scenario,
                original_publication_id=originals["publication_id"],
                corrected_publication_id=row["corrected"]["publication_id"],
                **{f"original_{k}": v for k, v in a.items()},
                **{f"corrected_{k}": v for k, v in b.items()},
                finding="CORRECTED_AUTHENTICATED",
                interpretation=(
                    "Changed holding inputs/terminal cycle plus cash-horizon repair; "
                    "not initial-NAV-only effect"
                ),
            )
        )
        if scenario == "BASE":
            facts.append(dict(method=method, original=a, corrected=b))
    # One narrowly predeclared paired comparison; no iid precision or superiority claim.
    for family, base in [("old", ARCHIVE), ("new", ROOT)]:
        curves = {}
        for method in ["equal_weight", "cvar"]:
            row = next(r for r in new_rows if r["scenario"] == "BASE" and r["method"] == method)
            manifest = (
                next(m for m in old_rows if m["publication_id"] == row["original_id"])
                if family == "old"
                else row["corrected"]
            )
            curve = table(base, manifest, "returns")
            curves[method] = curve.set_index("date").net_return
        paired = curves["cvar"] - curves["equal_weight"]
        leave = np.array([paired.drop(d).mean() for d in paired.index])
        checks.append(
            dict(
                kind="paired_CVaR_minus_equal_weight",
                source_category=family,
                n=len(paired),
                mean=float(paired.mean()),
                median=float(paired.median()),
                leave_one_out_min=float(leave.min()),
                leave_one_out_max=float(leave.max()),
                interpretation=(
                    "Descriptive matched-period sensitivity; "
                    "not a confidence interval or superiority test"
                ),
            )
        )
    return reconciliation, checks, facts


def corr(y, p):
    if np.ptp(y) == 0 or np.ptp(p) == 0:
        return None
    return float(np.corrcoef(rankdata(y), rankdata(p))[0, 1])


def fee_scenario_audit(old_rows, new_rows):
    records = []
    for method in sorted({r["method"] for r in new_rows}):
        for version, root in [("old", ARCHIVE), ("new", ROOT)]:
            weights = []
            net = []
            for scenario in ["LOW", "BASE", "HIGH"]:
                row = next(
                    r for r in new_rows if r["method"] == method and r["scenario"] == scenario
                )
                manifest = (
                    next(m for m in old_rows if m["publication_id"] == row["original_id"])
                    if version == "old"
                    else row["corrected"]
                )
                weights.append(
                    table(root, manifest, "allocations")
                    .sort_values(["date", "asset_id"])
                    .weight.to_numpy()
                )
                net.append(
                    read(artifact(root, manifest, "performance_summary"))["net_cumulative_return"]
                )
            error = max(float(np.max(np.abs(w - weights[1]))) for w in weights)
            assert error < 1e-10 and net[0] >= net[1] >= net[2]
            records.append(
                dict(
                    kind="fee_scenario_invariance",
                    method=method,
                    source_category=version,
                    low_return=net[0],
                    base_return=net[1],
                    high_return=net[2],
                    max_weight_difference=error,
                    interpretation="5/10/20bps per L1; same weights and monotonic fees",
                )
            )
    return records


def ml_audit(market, new_rows):
    folds, results, facts, prediction_tables = [], [], [], {}
    global_dates = pd.DatetimeIndex(sorted(pd.to_datetime(market.date, utc=True).unique()))
    daily = market.copy()
    daily.date = pd.to_datetime(daily.date, utc=True)
    complete = daily.pivot(index="date", columns="security_id", values="return").dropna()
    for row in new_rows:
        original = next(m for m in GATE["ml"] if m["publication_id"] == row["original_id"])
        summaries = {}
        for family, base, m in [("old", ARCHIVE, original), ("new", ROOT, row["corrected"])]:
            pred = table(base, m, "predictions")
            prediction_tables[(family, row["family"])] = pred
            evaluation = read(artifact(base, m, "evaluation"))
            comparison = read(artifact(base, m, "comparison"))
            econ = read(artifact(base, m, "economic_evaluation"))
            splits = table(base, m, "splits")
            targets = table(base, m, "targets")
            features = table(base, m, "feature_matrix")
            mergekeys = ["security_id", "formation_date", "fold"]
            assigned = splits.merge(
                targets.drop(columns=["target_start", "target_end"]),
                on=mergekeys,
                validate="one_to_one",
            )
            assigned = assigned.merge(features, on=mergekeys, validate="one_to_one")
            unique = targets.drop(columns="fold").drop_duplicates()
            months = (
                pd.to_datetime(unique.formation_date, utc=True)
                .dt.tz_localize(None)
                .dt.to_period("M")
            )
            positions = global_dates.get_indexer(pd.to_datetime(unique.formation_date, utc=True))
            full_horizon_errors = int(
                np.sum(
                    pd.to_datetime(unique.target_end, utc=True).to_numpy()
                    != global_dates[positions + 21].to_numpy()
                )
            )
            if family == "new":
                assert full_horizon_errors == 0
            ic_values = []
            net_values = []
            errors = []
            dates = sorted(pd.to_datetime(unique.formation_date, utc=True).unique())
            for f, g in assigned.groupby("fold", sort=True):
                train = g.loc[g.partition.eq("train")]
                val = g.loc[g.partition.eq("validation")]
                test = g.loc[g.partition.eq("test")]
                maxtrain = pd.to_datetime(train.target_end, utc=True).max()
                minval = pd.to_datetime(val.formation_date, utc=True).min()
                maxval = pd.to_datetime(val.target_end, utc=True).max()
                mintest = pd.to_datetime(test.formation_date, utc=True).min()
                assert maxtrain < minval and maxval < mintest
                trdates = sorted(pd.to_datetime(train.formation_date, utc=True).unique())
                vdates = sorted(pd.to_datetime(val.formation_date, utc=True).unique())
                tdates = sorted(pd.to_datetime(test.formation_date, utc=True).unique())
                assert len(vdates) == 12 and len(tdates) == 1
                assert dates.index(vdates[0]) - dates.index(trdates[-1]) - 1 == 1
                assert dates.index(tdates[0]) - dates.index(vdates[-1]) - 1 == 1
                q = pred.loc[pred.fold.eq(f)]
                y = q.target.to_numpy()
                forecast = q.prediction.to_numpy()
                coefficient = corr(y, forecast)
                if coefficient is not None:
                    ic_values.append(coefficient)
                ev = next(v for v in evaluation["folds"] if v["fold"] == f)["metrics"]
                expected = dict(
                    mae=float(np.mean(np.abs(y - forecast))),
                    rmse=float(np.sqrt(np.mean((y - forecast) ** 2))),
                    r_squared=float(1 - np.sum((y - forecast) ** 2) / np.sum((y - y.mean()) ** 2)),
                    spearman=coefficient,
                    directional_accuracy=float(np.mean(np.sign(y) == np.sign(forecast))),
                )
                for k, value in expected.items():
                    if value is None:
                        assert ev[k] is None or not np.isfinite(ev[k])
                    else:
                        errors.append(abs(value - ev[k]))
                        assert abs(value - ev[k]) < 1e-10
                position = complete.index.get_loc(pd.Timestamp(tdates[0]))
                nextdate = complete.index[position + 1]
                assert nextdate == global_dates[global_dates.get_loc(pd.Timestamp(tdates[0])) + 1]
                eligible = q.set_index("security_id").prediction.reindex(complete.columns).dropna()
                count = int(np.ceil(len(eligible) * 0.2))
                selected = eligible.nlargest(count).index
                gross = float(complete.loc[nextdate, selected].mean())
                fee = 0.001
                ec = next(v for v in econ["folds"] if v["fold"] == f)
                assert ec["return_rows"] == 1 and ec["transaction_rows"] == count
                error = max(
                    abs(ec["gross_cumulative_return"] - gross),
                    abs(ec["net_cumulative_return"] - (gross - fee)),
                    abs(ec["transaction_cost"] - fee),
                )
                assert error < 1e-12
                net_values.append(gross - fee)
                decisions = pd.to_datetime(test.formation_date, utc=True)
                expectedends = [global_dates[global_dates.get_loc(d) + 21] for d in decisions]
                wrong = int(
                    np.sum(
                        pd.to_datetime(test.target_end, utc=True).to_numpy()
                        != pd.DatetimeIndex(expectedends).to_numpy()
                    )
                )
                folds.append(
                    dict(
                        model=row["family"],
                        source_category=family,
                        fold=f,
                        publication_id=m["publication_id"],
                        unique_input_dates=len(dates),
                        calendar_months=int(months.nunique()),
                        unique_input_observations=len(unique),
                        train_start=trdates[0],
                        train_end=trdates[-1],
                        train_distinct_dates=len(trdates),
                        train_calendar_months=len(
                            pd.PeriodIndex(
                                pd.DatetimeIndex(trdates).tz_localize(None), freq="M"
                            ).unique()
                        ),
                        train_rows=len(train),
                        validation_start=minval,
                        validation_end=vdates[-1],
                        validation_rows=len(val),
                        test_date=tdates[0],
                        test_rows=len(test),
                        test_target_start=pd.to_datetime(test.target_start, utc=True).min(),
                        test_target_end=pd.to_datetime(test.target_end, utc=True).max(),
                        test_targets_available_by=pd.to_datetime(
                            test.target_available_at, utc=True
                        ).max(),
                        train_target_end=maxtrain,
                        validation_target_end=maxval,
                        train_validation_overlap=False,
                        validation_test_overlap=False,
                        purged_rows=int(g.partition.eq("purged").sum()),
                        embargo_train_validation_dates=1,
                        embargo_validation_test_dates=1,
                        test_horizon_violations=wrong,
                        ic=coefficient,
                        metric_max_error=max(errors) if errors else 0.0,
                        economic_return_date=nextdate,
                        economic_horizon_sessions=1,
                        target_horizon_sessions=21,
                        selected_securities=count,
                        initial_l1=1.0,
                        modeled_fee=fee,
                        economic_gross=gross,
                        economic_net=gross - fee,
                        economic_error=error,
                        timing_limit=(
                            "UTC-day features; same-close acquisition and "
                            "historical wall-clock forecasts not proven"
                        ),
                    )
                )
            processor = joblib.load(io.BytesIO(artifact(base, m, "preprocessor").read_bytes()))
            model = joblib.load(io.BytesIO(artifact(base, m, "model").read_bytes()))
            last = assigned.loc[
                assigned.fold.eq(assigned.fold.max()) & assigned.partition.eq("train")
            ]
            names = list(model.feature_names)
            values = last[names].to_numpy(float)
            assert np.allclose(processor.scaler.mean_, values.mean(axis=0), atol=1e-12, rtol=0)
            assert np.allclose(processor.scaler.scale_, values.std(axis=0), atol=1e-12, rtol=0)
            testlast = pred.loc[pred.fold.eq(pred.fold.max())]
            testfeatures = assigned.loc[
                assigned.fold.eq(assigned.fold.max()) & assigned.partition.eq("test")
            ].set_index(["security_id", "formation_date"])
            testfeatures = testfeatures.reindex(
                pd.MultiIndex.from_frame(testlast[["security_id", "formation_date"]])
            )
            x = processor.transform(testfeatures[names]).to_numpy(float)
            assert (
                np.max(
                    np.abs(model.predict(x, model.feature_names) - testlast.prediction.to_numpy())
                )
                < 1e-10
            )
            expl = table(base, m, "explanations")
            reference_prediction_error = None
            selected_parameters = []
            if row["family"] in {"zero", "historical_mean", "factor_composite", "linear", "ridge"}:
                reference_prediction_error = 0.0
                trials = read(artifact(base, m, "hyperparameter_trials"))["trials"]
                for fold_number, group in assigned.groupby("fold"):
                    tr = group.loc[group.partition.eq("train")]
                    qp = pred.loc[pred.fold.eq(fold_number)]
                    te = group.loc[group.partition.eq("test")].set_index(
                        ["security_id", "formation_date"]
                    )
                    te = te.reindex(pd.MultiIndex.from_frame(qp[["security_id", "formation_date"]]))
                    mean = tr[names].mean().to_numpy()
                    scale = tr[names].std(ddof=0).to_numpy()
                    xtr = (tr[names].to_numpy() - mean) / scale
                    xte = (te[names].to_numpy() - mean) / scale
                    ytr = tr.target.to_numpy()
                    params = {}
                    candidates = [t["parameters"] for t in trials if t["fold"] == fold_number]
                    preprocessor_id = expl.loc[expl.fold.eq(fold_number), "preprocessor_hash"].iloc[
                        0
                    ]
                    expected_id = qp.model_id.iloc[0]
                    for candidate in candidates:
                        value = (
                            f"{row['family']}|regression|{tuple(names)}|{preprocessor_id}|"
                            f"{m['target_hash']}|17|{sorted(candidate.items())}"
                        )
                        if (
                            "model-" + hashlib.sha256(value.encode()).hexdigest()[:32]
                            == expected_id
                        ):
                            params = candidate
                            break
                    else:
                        raise AssertionError(
                            (row["family"], fold_number, "Selected parameter identity absent")
                        )
                    if row["family"] == "zero":
                        reference = np.zeros(len(qp))
                    elif row["family"] == "historical_mean":
                        reference = np.full(len(qp), ytr.mean())
                    else:
                        intercept = ytr.mean() if params.get("fit_intercept", True) else 0.0
                        penalty = float(params.get("alpha", 0.0))
                        beta = np.linalg.solve(
                            xtr.T @ xtr + penalty * np.eye(len(names)), xtr.T @ (ytr - intercept)
                        )
                        reference = xte @ beta + intercept
                        coefficient = (
                            expl.loc[expl.fold.eq(fold_number) & expl.method.eq("coefficient")]
                            .set_index("feature")
                            .value.reindex(names)
                        )
                        assert np.max(np.abs(beta - coefficient.to_numpy())) < 1e-10
                    error = float(np.max(np.abs(reference - qp.prediction.to_numpy())))
                    assert error < 1e-10, (row["family"], fold_number, error)
                    reference_prediction_error = max(reference_prediction_error, error)
                    selected_parameters.append(dict(fold=int(fold_number), parameters=params))
            disagreements = []
            for _f, g in expl.groupby("fold"):
                perm = g.loc[g.method.eq("permutation")].groupby("feature").value.mean()
                shap = (
                    g.loc[g.method.eq("shap")]
                    .assign(absolute=lambda x: x.value.abs())
                    .groupby("feature")
                    .absolute.mean()
                )
                if len(perm) and len(shap):
                    disagreements.append(bool(perm.idxmax() != shap.idxmax()))
            interval = comparison["selected_model_bootstrap_ic"]
            date_ic = np.array(
                [
                    np.nan
                    if corr(q.target.to_numpy(), q.prediction.to_numpy()) is None
                    else corr(q.target.to_numpy(), q.prediction.to_numpy())
                    for _, q in pred.groupby("formation_date", sort=True)
                ]
            )
            reference_interval = dict(estimate=None, lower=None, upper=None)
            if np.isfinite(date_ic).any():
                rng = np.random.default_rng(17)
                bootstrap_values = []
                for _ in range(100):
                    indices = []
                    while len(indices) < len(date_ic):
                        start = int(rng.integers(0, max(1, len(date_ic) - 3 + 1)))
                        indices.extend(range(start, min(start + 3, len(date_ic))))
                    chosen = date_ic[indices[: len(date_ic)]]
                    if np.isfinite(chosen).any():
                        bootstrap_values.append(float(np.nanmean(chosen)))
                reference_interval = dict(
                    estimate=float(np.nanmean(date_ic)),
                    lower=float(np.quantile(bootstrap_values, 0.025)),
                    upper=float(np.quantile(bootstrap_values, 0.975)),
                )
            if family == "new":
                for key, value in reference_interval.items():
                    if value is None:
                        assert interval[key] is None
                    else:
                        assert abs(value - interval[key]) < 1e-12
            summaries[family] = dict(
                test_observations=len(pred),
                folds=len(evaluation["folds"]),
                valid_ic_folds=len(ic_values),
                mean_ic=float(np.mean(ic_values)) if ic_values else None,
                median_ic=float(np.median(ic_values)) if ic_values else None,
                ic_lag1=float(pd.Series(ic_values).autocorr()) if len(ic_values) > 2 else None,
                bootstrap_estimate=interval["estimate"],
                bootstrap_lower=interval["lower"],
                bootstrap_upper=interval["upper"],
                same_predictions_date_ic_lower=reference_interval["lower"],
                same_predictions_date_ic_upper=reference_interval["upper"],
                target_calendar_errors=full_horizon_errors,
                mean_one_session_net=float(np.mean(net_values)),
                positive_economic_folds=int(np.sum(np.array(net_values) > 0)),
                mean_initial_fee=0.001,
                mean_rmse=float(np.mean([f["metrics"]["rmse"] for f in evaluation["folds"]])),
                shap_permutation_top_disagreement_folds=sum(disagreements),
                explanation_comparable_folds=len(disagreements),
                final_coefficients=str(getattr(model.estimator, "coef_", None)),
                final_alpha=getattr(model.estimator, "alpha", None),
                reference_prediction_max_error=reference_prediction_error,
                selected_parameters=selected_parameters,
                final_feature_correlation=float(np.corrcoef(values.T)[0, 1]),
                prediction_reproduction_error=float(
                    np.max(
                        np.abs(
                            model.predict(x, model.feature_names) - testlast.prediction.to_numpy()
                        )
                    )
                ),
            )
            if family == "new":
                assert (
                    len(dates) == 89 and months.nunique() == 89 and len(evaluation["folds"]) == 15
                )
                assert wrong == 0
        results.append(
            dict(
                model=row["family"],
                original_publication_id=original["publication_id"],
                corrected_publication_id=row["corrected"]["publication_id"],
                **{f"original_{k}": v for k, v in summaries["old"].items()},
                **{f"corrected_{k}": v for k, v in summaries["new"].items()},
                evidence_status="CORRECTED_AUTHENTICATED",
                economic_limit=(
                    "Isolated one-session reset folds, not a continuous 21-session strategy"
                ),
            )
        )
        facts.append(
            dict(model=row["family"], original=summaries["old"], corrected=summaries["new"])
        )
    equivalence = []
    for family in ["old", "new"]:
        for a, b in [
            ("linear", "factor_composite"),
            ("linear", "ridge"),
            ("zero", "historical_mean"),
        ]:
            x = prediction_tables[(family, a)]
            y = prediction_tables[(family, b)]
            z = x.merge(
                y,
                on=["security_id", "formation_date", "fold"],
                suffixes=("_a", "_b"),
                validate="one_to_one",
            )
            for f, g in z.groupby("fold"):
                da = g.prediction_a.to_numpy()
                db = g.prediction_b.to_numpy()
                equivalence.append(
                    dict(
                        kind="prediction_equivalence",
                        source_category=family,
                        model_a=a,
                        model_b=b,
                        fold=int(f),
                        max_prediction_difference=float(np.max(np.abs(da - db))),
                        same_ranks=bool(np.array_equal(rankdata(da), rankdata(db))),
                        prediction_correlation=float(np.corrcoef(da, db)[0, 1])
                        if np.ptp(da) > 0 and np.ptp(db) > 0
                        else None,
                    )
                )
    for result in results:
        original = prediction_tables[("old", result["model"])]
        corrected = prediction_tables[("new", result["model"])]
        paired = original.merge(
            corrected,
            on=["security_id", "formation_date"],
            suffixes=("_old", "_new"),
            validate="one_to_one",
        )
        assert len(paired) == len(corrected)
        assert np.max(np.abs(paired.target_old - paired.target_new)) < 1e-12
        old_ic = [
            corr(g.target_new.to_numpy(), g.prediction_old.to_numpy())
            for _, g in paired.groupby("formation_date")
        ]
        old_ic = [v for v in old_ic if v is not None]
        result["original_ic_on_corrected_sample"] = float(np.mean(old_ic)) if old_ic else None
        result["matched_corrected_test_rows"] = len(paired)
    return folds, results, facts, equivalence


def main():
    assert_unchanged_sources()
    new_port = read(WORK / "corrected_portfolios.json")
    new_ml = read(WORK / "corrected_ml.json")
    assert len(new_port) == 24 and len(new_ml) == 8
    source_records = []
    for row in new_port:
        m = PortfolioRepository(ROOT, ROOT / "data/portfolio_manifests").authenticate(
            row["corrected"]["publication_id"]
        )
        assert m.content_hash() == PortfolioManifestHash(row["corrected"])
        source_records.append(m.model_dump(mode="json"))
    for row in new_ml:
        m = MLRepository(ROOT, ROOT / "data/ml_manifests").authenticate(
            row["corrected"]["publication_id"]
        )
        source_records.append(m.model_dump(mode="json"))
    market = pd.read_parquet(MARKET_PATH)
    market.date = pd.to_datetime(market.date)
    cache = WORK / "portfolio_verification_cache.json"
    if cache.exists():
        cached = read(cache)
        assert cached["corrected_ids"] == [r["corrected"]["publication_id"] for r in new_port]
        port, costs, pfacts = cached["port"], cached["costs"], cached["facts"]
    else:
        port, costs, pfacts = portfolio_audit(market, GATE["portfolio"], new_port)
        cache.write_bytes(
            (
                json.dumps(
                    dict(
                        corrected_ids=[r["corrected"]["publication_id"] for r in new_port],
                        port=port,
                        costs=costs,
                        facts=pfacts,
                    ),
                    indent=2,
                    default=str,
                )
                + "\n"
            ).encode()
        )
    folds, ml, mfacts, equivalence = ml_audit(market, new_ml)
    costs = [r for r in costs if r["kind"] != "fee_scenario_invariance"] + fee_scenario_audit(
        GATE["portfolio"], new_port
    )
    OUT.mkdir(parents=True, exist_ok=True)
    pd.DataFrame(port).to_csv(
        OUT / "PHASE3_PORTFOLIO_RECONCILIATION.csv", index=False, lineterminator="\n"
    )
    pd.DataFrame(costs).to_csv(
        OUT / "PHASE3_TRADE_COST_AND_RISK_CHECKS.csv", index=False, lineterminator="\n"
    )
    pd.DataFrame(folds).to_csv(
        OUT / "PHASE3_ML_FOLD_AND_LEAKAGE_AUDIT.csv", index=False, lineterminator="\n"
    )
    pd.DataFrame(ml).to_csv(
        OUT / "PHASE3_ML_RESULTS_RECONCILIATION.csv", index=False, lineterminator="\n"
    )
    (WORK / "verification_facts.json").write_bytes(
        (
            json.dumps(
                dict(
                    portfolio=pfacts,
                    ml=mfacts,
                    equivalence=equivalence,
                    publications=source_records,
                ),
                indent=2,
                default=str,
            )
            + "\n"
        ).encode()
    )
    assert_unchanged_sources()
    print(
        "PASS: historical/corrected accounting, risk, objectives, folds, predictions and economics"
    )


def PortfolioManifestHash(value):
    return hashlib.sha256(
        json.dumps(value, sort_keys=True, separators=(",", ":")).encode()
    ).hexdigest()


if __name__ == "__main__":
    main()
