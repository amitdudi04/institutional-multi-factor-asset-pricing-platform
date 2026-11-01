"""Known mathematical identities and adversarial independent-reference tests."""

import runpy
from pathlib import Path

import numpy as np
import pytest

REFERENCE = runpy.run_path(str(Path(__file__).parents[1] / "scripts/phase2c_reference.py"))
fit = REFERENCE["reference_fit"]
holm = REFERENCE["holm"]


def test_high_fit_and_negative_alpha_are_compatible() -> None:
    x = np.linspace(-0.1, 0.2, 80)
    z = np.sin(np.arange(80) * 1.7)
    design = np.column_stack([np.ones(80), x])
    noise = z - design @ np.linalg.lstsq(design, z, rcond=None)[0]
    y = -0.002 + 1.2 * x + 0.01 * noise
    result = fit(y, x[:, None])
    assert result["beta"] == pytest.approx([-0.002, 1.2], abs=1e-12)
    assert result["r2"] > 0.98
    assert result["alpha_mean_identity"] == pytest.approx(-0.002, abs=1e-12)
    assert result["normal_scaled"] < 1e-12
    assert result["adj"] == pytest.approx(1 - (1 - result["r2"]) * 79 / 78)


def test_qr_pivot_and_hac0_independent_sandwich() -> None:
    rng = np.random.default_rng(52)
    factors = rng.normal(size=(75, 3)) * [0.001, 2.0, 0.05]
    y = -0.003 + factors @ np.array([2.0, 0.01, 0.3]) + rng.normal(size=75) * 0.02
    result = fit(y, factors, lag=0)
    design = np.column_stack([np.ones(75), factors])
    beta = np.linalg.lstsq(design, y, rcond=None)[0]
    e = y - design @ beta
    inverse = np.linalg.inv(design.T @ design)
    expected = inverse @ ((design * e[:, None]).T @ (design * e[:, None])) @ inverse * 75 / 71
    assert result["beta"] == pytest.approx(beta, abs=1e-10)
    np.testing.assert_allclose(result["covariance"], expected, atol=1e-10)
    assert result["df"] == 71
    assert np.all(result["lower"] <= result["beta"])
    assert np.all(result["upper"] >= result["beta"])


@pytest.mark.parametrize("case", ["rank", "nan", "short", "lag", "constant_y"])
def test_reference_fails_closed(case: str) -> None:
    x = np.arange(40, dtype=float)[:, None]
    y = np.sin(x[:, 0])
    kwargs = {}
    if case == "rank":
        x = np.column_stack([x, x])
    elif case == "nan":
        x[3] = np.nan
    elif case == "short":
        x, y = x[:10], y[:10]
    elif case == "lag":
        kwargs["lag"] = 40
    else:
        y[:] = 1.0
    with pytest.raises(ValueError):
        fit(y, x, **kwargs)


def test_holm_arbitrary_dependence_adjustment() -> None:
    assert holm([0.04, 0.001, 0.01]) == pytest.approx([0.04, 0.003, 0.02])
    with pytest.raises(ValueError):
        holm([np.nan])
