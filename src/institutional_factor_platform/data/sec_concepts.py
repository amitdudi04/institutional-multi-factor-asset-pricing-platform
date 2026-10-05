"""SEC XBRL concept vocabulary for point-in-time fundamental projection."""

from dataclasses import dataclass
from enum import StrEnum


class SecFieldMethod(StrEnum):
    """How a supported fundamental field may be obtained from SEC facts."""

    DIRECT = "DIRECT"
    COMPONENT_SUM = "COMPONENT_SUM"
    DIFFERENCE = "DIFFERENCE"
    LAG = "LAG"
    AVERAGE = "AVERAGE"
    NOT_ESTIMABLE = "NOT_ESTIMABLE"


@dataclass(frozen=True, slots=True)
class SecConceptRule:
    """Ordered standard-taxonomy concepts and an explicit calculation policy."""

    field: str
    method: SecFieldMethod
    primary_concepts: tuple[str, ...] = ()
    fallback_concepts: tuple[str, ...] = ()
    unit: str = "USD"
    calculation: str | None = None

    def select_concept(self, observed: set[str]) -> str | None:
        """Select only a configured standard concept, in precedence order."""
        if self.method is not SecFieldMethod.DIRECT:
            return None
        return next(
            (
                concept
                for concept in self.primary_concepts + self.fallback_concepts
                if concept in observed
            ),
            None,
        )


SEC_XBRL_CONCEPT_REGISTRY: dict[str, SecConceptRule] = {
    "book_equity": SecConceptRule(
        "book_equity",
        SecFieldMethod.DIRECT,
        ("StockholdersEquity",),
        ("StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",),
    ),
    "net_income": SecConceptRule(
        "net_income", SecFieldMethod.DIRECT, ("NetIncomeLoss",), ("ProfitLoss",)
    ),
    "operating_cash_flow": SecConceptRule(
        "operating_cash_flow",
        SecFieldMethod.DIRECT,
        ("NetCashProvidedByUsedInOperatingActivities",),
    ),
    "dividends": SecConceptRule(
        "dividends",
        SecFieldMethod.DIRECT,
        ("PaymentsOfDividendsCommonStock",),
        ("PaymentsOfDividends",),
    ),
    "shareholder_equity": SecConceptRule(
        "shareholder_equity",
        SecFieldMethod.DIRECT,
        ("StockholdersEquity",),
        ("StockholdersEquityIncludingPortionAttributableToNoncontrollingInterest",),
    ),
    "total_assets": SecConceptRule("total_assets", SecFieldMethod.DIRECT, ("Assets",)),
    "gross_profit": SecConceptRule("gross_profit", SecFieldMethod.DIRECT, ("GrossProfit",)),
    "operating_income": SecConceptRule(
        "operating_income", SecFieldMethod.DIRECT, ("OperatingIncomeLoss",)
    ),
    "revenue": SecConceptRule(
        "revenue",
        SecFieldMethod.DIRECT,
        ("RevenueFromContractWithCustomerExcludingAssessedTax",),
        ("Revenues", "SalesRevenueNet"),
    ),
    "average_assets": SecConceptRule(
        "average_assets",
        SecFieldMethod.AVERAGE,
        calculation="mean(total_assets, prior_total_assets); both observations required",
    ),
    "total_accruals": SecConceptRule(
        "total_accruals",
        SecFieldMethod.DIFFERENCE,
        calculation="net_income - operating_cash_flow; both observations required",
    ),
    "total_debt": SecConceptRule(
        "total_debt",
        SecFieldMethod.COMPONENT_SUM,
        (
            "LongTermDebtCurrent",
            "LongTermDebtNoncurrent",
        ),
        (
            "LongTermDebtAndFinanceLeaseObligationsCurrent",
            "LongTermDebtAndFinanceLeaseObligationsNoncurrent",
        ),
        calculation="one internally consistent current/noncurrent concept family; no overlap",
    ),
    "interest_expense": SecConceptRule(
        "interest_expense",
        SecFieldMethod.DIRECT,
        ("InterestExpenseNonOperating",),
        ("InterestAndDebtExpense",),
    ),
    "prior_total_assets": SecConceptRule(
        "prior_total_assets",
        SecFieldMethod.LAG,
        calculation="prior eligible annual total_assets observation; no forward fill",
    ),
    "capex": SecConceptRule(
        "capex",
        SecFieldMethod.DIRECT,
        ("PaymentsToAcquirePropertyPlantAndEquipment",),
    ),
    "prior_capex": SecConceptRule(
        "prior_capex",
        SecFieldMethod.LAG,
        calculation="prior eligible annual capex observation; no forward fill",
    ),
    "net_equity_issuance": SecConceptRule(
        "net_equity_issuance",
        SecFieldMethod.NOT_ESTIMABLE,
        calculation=(
            "not estimable until a complete mutually exclusive issuance/repurchase component "
            "policy is validated; missing components are never zero-filled"
        ),
    ),
    "working_capital": SecConceptRule(
        "working_capital",
        SecFieldMethod.DIFFERENCE,
        ("AssetsCurrent", "LiabilitiesCurrent"),
        calculation="AssetsCurrent - LiabilitiesCurrent; both observations required",
    ),
    "prior_working_capital": SecConceptRule(
        "prior_working_capital",
        SecFieldMethod.LAG,
        calculation="prior eligible annual working_capital observation; no forward fill",
    ),
}


ACCEPTED_SEC_FORMS = frozenset({"10-K", "10-K/A", "10-Q", "10-Q/A"})
ANNUAL_SEC_FORMS = frozenset({"10-K", "10-K/A"})
