"""Independent economic identities for the frozen Phase 2B policy."""

import hashlib
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

from institutional_factor_platform.data.bound import authenticate_supplementary
from institutional_factor_platform.exceptions import DataQualityError, EvidenceIntegrityError
from institutional_factor_platform.factors.holding import (
    endpoint_chain,
    form_quantiles,
    matched_sample,
    monthly_cycles,
    validate_session_series,
)


def quotes() -> pd.DataFrame:
    return pd.DataFrame(
        {
            "date": pd.date_range("2024-01-02", periods=4, freq="B"),
            "price": [100.0, 90.0, 99.0, 110.0],
            "return": [0.0, -0.1, 0.1, 110 / 99 - 1],
        }
    )


def test_full_and_interior_gap_identity() -> None:
    q = quotes()
    sessions = pd.DatetimeIndex(q.date)
    full, status, _ = endpoint_chain(q, sessions[0], sessions[-1], sessions)
    assert full == pytest.approx(0.1)
    assert status == "COMPLETE_VALID"
    q = q.drop(index=1)
    q.loc[2, "return"] = -0.01  # next genuine quote bridges the missing session
    value, status, count = endpoint_chain(q, sessions[0], sessions[-1], sessions)
    assert value == pytest.approx(0.1)
    assert (status, count) == ("COMPLETE_VALID", 3)


@pytest.mark.parametrize("missing", [0, 3])
def test_no_unauthenticated_terminal_or_entry(missing: int) -> None:
    q = quotes()
    sessions = pd.DatetimeIndex(q.date)
    value, reason, _ = endpoint_chain(q.drop(index=missing), sessions[0], sessions[-1], sessions)
    assert value is None
    assert reason == "MISSING_ENDPOINT_NO_AUTHENTIC_TERMINAL"


@pytest.mark.parametrize(
    "column,value,reason",
    [
        ("price", 0.0, "INVALID_QUOTE"),
        ("price", np.nan, "INVALID_QUOTE"),
        ("return", np.inf, "UNRECONCILED_QUOTE_RETURN_CHAIN"),
        ("return", -1.0, "UNRECONCILED_QUOTE_RETURN_CHAIN"),
        ("return", 0.5, "UNRECONCILED_QUOTE_RETURN_CHAIN"),
    ],
)
def test_invalid_links_reject(column: str, value: float, reason: str) -> None:
    q = quotes()
    sessions = pd.DatetimeIndex(q.date)
    q.loc[1, column] = value
    assert endpoint_chain(q, sessions[0], sessions[-1], sessions)[1] == reason


def test_duplicate_and_non_session_quotes() -> None:
    q = quotes()
    sessions = pd.DatetimeIndex(q.date)
    with pytest.raises(DataQualityError, match="Duplicate"):
        endpoint_chain(pd.concat([q, q.iloc[:1]]), sessions[0], sessions[-1], sessions)
    with pytest.raises(DataQualityError, match="outside"):
        endpoint_chain(q, sessions[0], sessions[-1], sessions.delete(1))


def test_membership_fixed_before_future_inspection() -> None:
    frame = pd.DataFrame(
        {
            "factor_id": ["x"] * 5 + ["sparse"] * 2,
            "security_id": list("abcdefg"),
            "score_value": range(7),
            "market_cap": [1.0, 2.0, 3.0, 4.0, 5.0, 1.0, 1.0],
            "eligible": [True, True, True, False, True, True, True],
        }
    )
    members = form_quantiles(frame)
    assert set(members.security_id) == set("abce")
    assert members.groupby("quantile").weight.sum().tolist() == [1.0, 1.0, 1.0]
    # Losing an endpoint after formation must not rerank or normalize survivors.
    assert members.set_index("security_id").loc["c", "weight"] == pytest.approx(3 / 8)
    with pytest.raises(DataQualityError, match="Duplicate"):
        form_quantiles(pd.concat([frame, frame.iloc[:1]]))


def test_next_session_execution_and_no_terminal_partial() -> None:
    sessions = pd.bdate_range("2024-01-01", "2024-04-30")
    cycles = monthly_cycles(sessions)
    assert cycles[0] == (
        pd.Timestamp("2024-01-31"),
        pd.Timestamp("2024-02-01"),
        pd.Timestamp("2024-03-01"),
    )
    assert cycles[-1][-1] == pd.Timestamp("2024-04-01")
    assert all(end <= sessions[-1] for _, _, end in cycles)


def test_common_calendar_and_cash_contract() -> None:
    q = quotes().assign(security_id="a", market_return=0.01, risk_free_rate=0.001)
    sessions = pd.DatetimeIndex(q.date)
    daily = validate_session_series(q, sessions)
    assert (1 + daily.risk_free_rate).prod() - 1 == pytest.approx(1.001**4 - 1)
    for bad in [
        q.iloc[:-1],
        pd.concat([q, q.iloc[:1]]),
        q.assign(market_return=np.nan),
        q.assign(risk_free_rate=-1.0),
    ]:
        with pytest.raises(DataQualityError):
            validate_session_series(bad, sessions)
    conflicting = pd.concat([q, q.assign(security_id="b", risk_free_rate=0.002)])
    with pytest.raises(DataQualityError, match="Conflicting"):
        validate_session_series(conflicting, sessions)


def test_common_sample_removes_missing_for_all_models() -> None:
    frame = pd.DataFrame(
        {
            "asset_id": ["x"] * 3,
            "date": range(3),
            "excess_return": [0.1, 0.2, 0.3],
            "m": [1.0, 2.0, 3.0],
            "h": [1.0, np.nan, 3.0],
        }
    )
    assert matched_sample(frame, ("m", "h")).date.tolist() == [0, 2]
    with pytest.raises(DataQualityError, match="Duplicate"):
        matched_sample(pd.concat([frame, frame.iloc[:1]]), ("m",))


def test_bound_memberships_cannot_change_or_escape(tmp_path: Path) -> None:
    path = tmp_path / "memberships"
    path.write_bytes(b"fixed")
    item = {"path": path.name, "bytes": 5, "sha256": hashlib.sha256(b"fixed").hexdigest()}
    authenticate_supplementary({}, tmp_path)
    authenticate_supplementary({"bound_supplementary_artifacts": [item]}, tmp_path)
    for items in [
        [item, item],
        [{**item, "path": "../outside"}],
        [{**item, "sha256": "bad"}],
        [{"path": "missing"}],
    ]:
        with pytest.raises(EvidenceIntegrityError):
            authenticate_supplementary({"bound_supplementary_artifacts": items}, tmp_path)
    path.write_bytes(b"other")
    with pytest.raises(EvidenceIntegrityError):
        authenticate_supplementary({"bound_supplementary_artifacts": [item]}, tmp_path)
