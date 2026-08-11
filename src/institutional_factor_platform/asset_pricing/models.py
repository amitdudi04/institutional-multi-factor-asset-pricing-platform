"""Approved and custom empirical asset-pricing model specifications."""

from dataclasses import dataclass

from institutional_factor_platform.exceptions import ConfigurationError


@dataclass(frozen=True, slots=True)
class ModelSpec:
    model_id: str
    factors: tuple[str, ...]
    equation: str
    dependent_variable: str = "excess_return"
    frequency: str = "monthly"
    return_unit: str = "decimal_return"

    def __post_init__(self) -> None:
        if not self.model_id or not self.factors or len(set(self.factors)) != len(self.factors):
            raise ConfigurationError("Model specifications require a name and unique factors.")
        if self.dependent_variable != "excess_return":
            raise ConfigurationError(
                "Asset-pricing models require excess_return as the dependent variable."
            )
        if self.frequency != "monthly":
            raise ConfigurationError("Asset-pricing models require monthly input frequency.")
        if self.return_unit != "decimal_return":
            raise ConfigurationError("Asset-pricing models require decimal_return inputs.")


MODEL_SPECS: dict[str, ModelSpec] = {
    "capm": ModelSpec("capm", ("market_excess",), "R_i-R_f = alpha + beta_m(MKT-R_f) + e"),
    "fama_french_3": ModelSpec(
        "fama_french_3",
        ("market_excess", "SMB", "HML"),
        "R_i-R_f = alpha + beta_m MKT + beta_s SMB + beta_h HML + e",
    ),
    "carhart_4": ModelSpec(
        "carhart_4",
        ("market_excess", "SMB", "HML", "MOM"),
        "R_i-R_f = alpha + beta_m MKT + beta_s SMB + beta_h HML + beta_w MOM + e",
    ),
    "fama_french_5": ModelSpec(
        "fama_french_5",
        ("market_excess", "SMB", "HML", "RMW", "CMA"),
        "R_i-R_f = alpha + beta_m MKT + beta_s SMB + beta_h HML + beta_r RMW + beta_c CMA + e",
    ),
    "hou_xue_zhang_q": ModelSpec(
        "hou_xue_zhang_q",
        ("market_excess", "ME", "IA", "ROE"),
        "R_i-R_f = alpha + beta_m MKT + beta_me ME + beta_ia IA + beta_roe ROE + e",
    ),
}


def custom_model(
    model_id: str,
    factors: tuple[str, ...],
    *,
    dependent_variable: str = "excess_return",
    frequency: str = "monthly",
    return_unit: str = "decimal_return",
) -> ModelSpec:
    """Create an explicit custom model without changing the approved registry."""
    return ModelSpec(
        model_id,
        factors,
        "excess_return = alpha + factor loadings + e",
        dependent_variable,
        frequency,
        return_unit,
    )
