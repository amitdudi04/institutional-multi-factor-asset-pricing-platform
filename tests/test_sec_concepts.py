from institutional_factor_platform.data.sec_concepts import (
    ACCEPTED_SEC_FORMS,
    SEC_XBRL_CONCEPT_REGISTRY,
    SecFieldMethod,
)
from institutional_factor_platform.factors.contracts import REQUIRED_FUNDAMENTAL_FIELDS


def test_sec_registry_exactly_covers_phase2_vocabulary() -> None:
    assert set(SEC_XBRL_CONCEPT_REGISTRY) == set(REQUIRED_FUNDAMENTAL_FIELDS)
    assert ACCEPTED_SEC_FORMS == {"10-K", "10-K/A", "10-Q", "10-Q/A"}
    assert all(rule.field == field for field, rule in SEC_XBRL_CONCEPT_REGISTRY.items())
    assert all(rule.unit == "USD" for rule in SEC_XBRL_CONCEPT_REGISTRY.values())


def test_sec_registry_uses_ordered_standard_concepts_and_fails_closed() -> None:
    revenue = SEC_XBRL_CONCEPT_REGISTRY["revenue"]
    assert revenue.select_concept({"Revenues", "SalesRevenueNet"}) == "Revenues"
    assert (
        revenue.select_concept({"Revenues", "RevenueFromContractWithCustomerExcludingAssessedTax"})
        == "RevenueFromContractWithCustomerExcludingAssessedTax"
    )
    assert revenue.select_concept({"RegistrantDefinedRevenue"}) is None
    assert SEC_XBRL_CONCEPT_REGISTRY["working_capital"].method is SecFieldMethod.DIFFERENCE
    assert (
        SEC_XBRL_CONCEPT_REGISTRY["working_capital"].select_concept(
            {"AssetsCurrent", "LiabilitiesCurrent"}
        )
        is None
    )
    assert SEC_XBRL_CONCEPT_REGISTRY["net_equity_issuance"].method is SecFieldMethod.NOT_ESTIMABLE
