from __future__ import annotations

from datetime import date
from typing import Annotated, Literal
from uuid import UUID

from pydantic import AliasChoices, BaseModel, ConfigDict, Field, model_validator

AccountClass = Literal["BUDGET", "TRACKING", "INVESTMENT", "LOAN", "TANGIBLE_ASSET"]
BudgetAccountType = Literal["DEPOSIT", "CREDIT_CARD"]
InvestmentTaxTreatment = Literal[
    "TAXABLE_BROKERAGE",
    "TRADITIONAL_IRA",
    "ROTH_IRA",
    "SEP_IRA",
    "SIMPLE_IRA",
    "TRADITIONAL_401K",
    "ROTH_401K",
    "TRADITIONAL_403B",
    "ROTH_403B",
    "TRADITIONAL_457B",
    "ROTH_457B",
    "HSA",
    "EDUCATION_529",
    "CUSTODIAL",
    "OTHER_TAX_ADVANTAGED",
]
TransactionStatus = Literal["PENDING", "CLEARED"]
SystemCategory = Literal[
    "TX_AVAILABLE_TO_BUDGET",
    "TX_STARTING_BALANCE",
    "TX_ACCOUNT_TRANSFER",
    "TX_BALANCE_ADJUSTMENT",
]
CategoryKind = Literal["STANDARD", "CREDIT_CARD_PAYMENT"]


class ImportRequest(BaseModel):
    sheet_url_or_id: str = Field(min_length=1)


NetWorthTreatment = Literal[
    "DUPLICATE_BUDGET_ACCOUNT",
    "IMPORT_TRACKING_ACCOUNT",
    "DO_NOT_IMPORT",
]
TrackingPolarity = Literal["ASSET", "LIABILITY"]
ReviewConfidence = Literal["HIGH", "MEDIUM", "LOW", "NONE"]


class ImportReviewDecision(BaseModel):
    raw_name: str
    treatment: NetWorthTreatment
    matched_account_id: str | None = None
    polarity: TrackingPolarity | None = None


class ImportCommitRequest(BaseModel):
    draft_id: str = Field(min_length=1)
    decisions: list[ImportReviewDecision]
    low_confidence_confirmed: bool = False


class AllocationRequest(BaseModel):
    date: date
    amount_minor: int = Field(gt=0)
    memo: str = ""
    from_bucket_id: str
    to_bucket_id: str


class FundCategoryRequest(BaseModel):
    client_operation_id: UUID
    date: date
    category_id: str
    amount_minor: int = Field(gt=0)
    memo: str = ""


class TransactionPayload(BaseModel):
    date: date
    account_id: str
    amount_minor: int
    category_id: str | None = None
    system_category: SystemCategory | None = None
    status: TransactionStatus
    memo: str = ""
    insert_after_transaction_id: str | None = None
    loan_account_id: str | None = None

    @model_validator(mode="after")
    def validate_category_choice(self) -> "TransactionPayload":
        if (self.category_id is None) == (self.system_category is None):
            raise ValueError("Exactly one of category_id or system_category must be set")
        return self


class TransferPayload(BaseModel):
    date: date
    from_account_id: str
    to_account_id: str
    amount_minor: int = Field(gt=0)
    status: TransactionStatus
    memo: str = ""


class AccountBudgetLinkPayload(BaseModel):
    category_id: str
    link_behavior: Literal["CREDIT_CARD_PAYMENT", "INVESTMENT_CONTRIBUTION", "LOAN_PAYMENT"]
    effective_date: date


class InvestmentTransferPayload(BaseModel):
    direction: Literal["CONTRIBUTION", "WITHDRAWAL"]
    client_operation_id: UUID
    source_account_id: str
    source_posted_date: date
    source_status: TransactionStatus
    destination_account_id: str
    destination_posted_date: date
    destination_status: TransactionStatus
    amount_minor: int = Field(gt=0)
    memo: str = ""


class CreditCardPaymentPayload(BaseModel):
    client_operation_id: UUID
    source_account_id: str
    source_posted_date: date
    source_status: TransactionStatus
    destination_account_id: str
    destination_posted_date: date
    destination_status: TransactionStatus
    amount_minor: int = Field(gt=0)
    memo: str = ""


class AccountPayload(BaseModel):
    name: str = Field(min_length=1)
    account_class: AccountClass
    budget_account_type: BudgetAccountType | None = None
    institution: str | None = None
    account_number_last4: str | None = None
    is_hidden: bool = False
    is_active: bool = True
    display_liability_positive: bool | None = None
    apy_minor: int | None = None
    polarity: str | None = None
    source: str | None = None
    self_managed: bool | None = None
    tax_treatment: InvestmentTaxTreatment | None = None
    original_amount_minor: int | None = None
    origination_date: str | None = None
    rate_minor: int | None = Field(default=None, ge=0)
    status: str | None = None
    opening_valuation_minor: int | None = None
    opening_valuation_date: str | None = None
    investment_contribution_category_id: str | None = None
    loan_payment_category_id: str | None = None
    current_principal_minor: int | None = Field(default=None, ge=0)
    current_principal_as_of: date | None = None
    rate_type: Literal["FIXED", "VARIABLE"] | None = None
    scheduled_principal_interest_minor: int | None = Field(default=None, gt=0)
    payment_frequency: Literal["MONTHLY", "BIWEEKLY", "WEEKLY"] | None = None
    next_payment_date: date | None = None
    maturity_date: date | None = None
    remaining_term_months: int | None = Field(default=None, gt=0)
    recurring_extra_principal_minor: int | None = Field(default=None, ge=0)

    @model_validator(mode="after")
    def validate_loan_opening_value(self) -> "AccountPayload":
        if self.account_class != "LOAN":
            return self
        required = {
            "current_principal_minor": self.current_principal_minor,
            "current_principal_as_of": self.current_principal_as_of,
            "loan_payment_category_id": self.loan_payment_category_id,
        }
        missing = [name for name, value in required.items() if value is None or value == ""]
        if missing:
            raise ValueError(f"Loan creation requires {', '.join(missing)}")
        return self


class AccountUpdatePayload(BaseModel):
    name: str | None = None
    is_hidden: bool | None = None
    is_active: bool | None = None
    institution: str | None = None
    account_number_last4: str | None = None
    apy_minor: int | None = None
    polarity: str | None = None
    source: str | None = None
    self_managed: bool | None = None
    tax_treatment: InvestmentTaxTreatment | None = None
    original_amount_minor: int | None = None
    origination_date: str | None = None
    rate_minor: int | None = Field(default=None, ge=0)
    loan_status: str | None = None
    rate_type: Literal["FIXED", "VARIABLE"] | None = None
    scheduled_principal_interest_minor: int | None = Field(default=None, gt=0)
    payment_frequency: Literal["MONTHLY", "BIWEEKLY", "WEEKLY"] | None = None
    next_payment_date: date | None = None
    maturity_date: date | None = None
    remaining_term_months: int | None = Field(default=None, gt=0)
    recurring_extra_principal_minor: int | None = Field(default=None, ge=0)


class CategoryGroupPayload(BaseModel):
    name: str = Field(min_length=1)
    sort_order: int
    is_hidden: bool = False


class CategoryGroupUpdatePayload(BaseModel):
    name: str | None = None
    sort_order: int | None = None
    is_hidden: bool | None = None


class CategoryPayload(BaseModel):
    group_id: str
    name: str = Field(min_length=1)
    category_kind: CategoryKind = "STANDARD"
    sort_order: int
    is_hidden: bool = False
    is_active: bool = True
    target_amount_minor: int | None = None
    due_date_rule: str | None = None
    goal_type: str | None = None
    goal_amount_minor: int | None = None
    goal_frequency: str | None = None
    goal_due_date: str | None = None
    icon: str | None = None


class CategoryUpdatePayload(BaseModel):
    model_config = ConfigDict(extra="forbid")

    group_id: str | None = None
    name: str | None = None
    sort_order: int | None = None
    is_hidden: bool | None = None
    is_active: bool | None = None
    target_amount_minor: int | None = None
    due_date_rule: str | None = None
    goal_type: str | None = None
    goal_amount_minor: int | None = None
    goal_frequency: str | None = None
    goal_due_date: str | None = None
    icon: str | None = None


class GoalPayload(BaseModel):
    goal_type: str | None = None
    goal_amount_minor: int | None = None
    goal_frequency: str | None = None
    goal_due_date: str | None = None


class TrackingAccountSnapshotPayload(BaseModel):
    effective_date: date
    amount_minor: int = Field(ge=0)
    source: str = "manual"
    notes: str = ""


class LoanBalanceSnapshotPayload(BaseModel):
    effective_date: date
    principal_balance_minor: int = Field(ge=0)
    accrued_interest_minor: int | None = Field(default=None, ge=0)
    escrow_balance_minor: int = Field(default=0, ge=0)
    unapplied_credit_minor: int | None = Field(default=None, ge=0)
    ytd_principal_paid_minor: int | None = Field(default=None, ge=0)
    ytd_interest_paid_minor: int | None = Field(default=None, ge=0)
    notes: str = ""


class LoanPaymentPayload(BaseModel):
    date: date
    budget_account_id: str
    amount_minor: int = Field(gt=0)
    status: TransactionStatus
    memo: str = "Loan payment"


class TangibleAssetValuationPayload(BaseModel):
    effective_date: date
    amount_minor: int = Field(ge=0)
    source: str = "manual"
    notes: str = ""


class InvestmentPositionPayload(BaseModel):
    effective_date: date
    ticker: str = Field(min_length=1)
    quantity_micros: int = Field(ge=0)
    average_basis_minor: int = Field(ge=0)


class InvestmentStatementHoldingPayload(BaseModel):
    ticker: str = Field(min_length=1)
    quantity_micros: int = Field(ge=0)
    price_minor: int = Field(gt=0)
    average_basis_minor: int = Field(ge=0)


class InvestmentStatementPayload(BaseModel):
    effective_date: date
    cash_balance_minor: int = Field(ge=0)
    holdings: list[InvestmentStatementHoldingPayload]
    notes: str = ""

    @model_validator(mode="after")
    def validate_unique_tickers(self) -> "InvestmentStatementPayload":
        tickers = [holding.ticker.strip().upper() for holding in self.holdings]
        if len(tickers) != len(set(tickers)):
            raise ValueError("Statement holdings must use unique tickers")
        return self


class InvestmentCashSnapshotPayload(BaseModel):
    effective_date: date
    cash_balance_minor: int
    notes: str = ""


class InvestmentPriceSnapshotPayload(BaseModel):
    account_id: str | None = None
    effective_date: date
    price_minor: int = Field(gt=0)
    source: str = "manual"


class InvestmentCutoverSuccessorPayload(BaseModel):
    account_class: Literal["INVESTMENT"]
    name: str = Field(min_length=1)
    institution: str | None = None
    account_number_last4: str | None = None
    self_managed: bool = False
    tax_treatment: InvestmentTaxTreatment = "TAXABLE_BROKERAGE"
    contribution_category_id: str | None = None
    cash_balance_minor: int = Field(ge=0)
    holdings: list[InvestmentStatementHoldingPayload] = Field(default_factory=list)


class LoanCutoverSuccessorPayload(BaseModel):
    account_class: Literal["LOAN"]
    name: str = Field(min_length=1)
    institution: str | None = None
    account_number_last4: str | None = None
    payment_category_id: str
    principal_balance_minor: int = Field(ge=0)
    accrued_interest_minor: int | None = Field(default=None, ge=0)
    escrow_balance_minor: int = Field(default=0, ge=0)
    unapplied_credit_minor: int | None = Field(default=None, ge=0)
    original_amount_minor: int | None = Field(default=None, ge=0)
    origination_date: date | None = None
    rate_minor: int | None = Field(default=None, ge=0)
    rate_type: Literal["FIXED", "VARIABLE"] | None = None
    scheduled_principal_interest_minor: int | None = Field(default=None, gt=0)
    payment_frequency: Literal["MONTHLY", "BIWEEKLY", "WEEKLY"] | None = None
    next_payment_date: date | None = None
    maturity_date: date | None = None
    remaining_term_months: int | None = Field(default=None, gt=0)
    recurring_extra_principal_minor: int | None = Field(default=None, ge=0)


class TangibleCutoverSuccessorPayload(BaseModel):
    account_class: Literal["TANGIBLE_ASSET"]
    name: str = Field(min_length=1)
    institution: str | None = None
    account_number_last4: str | None = None
    opening_value_minor: int = Field(ge=0)


CutoverSuccessorPayload = Annotated[
    InvestmentCutoverSuccessorPayload
    | LoanCutoverSuccessorPayload
    | TangibleCutoverSuccessorPayload,
    Field(discriminator="account_class"),
]


class TrackingCutoverPayload(BaseModel):
    operation_id: UUID
    cutover_date: date
    expected_predecessor_value_minor: int = Field(ge=0)
    final_predecessor_value_minor: int = Field(ge=0)
    successors: list[CutoverSuccessorPayload] = Field(min_length=1)


class ReconciliationSourceRecordPayload(BaseModel):
    source_record_id: str = Field(min_length=1)
    posted_date: date
    cleared_date: date | None = None
    signed_amount_minor: int
    source_status: TransactionStatus
    description: str = ""
    transaction_id: UUID | None = None
    raw_payload: dict[str, object] | None = None


class ReconciliationDraftPayload(BaseModel):
    source_kind: Literal["BANK_STATEMENT", "CREDIT_CARD_STATEMENT", "INVESTMENT_STATEMENT"]
    period_start: date | None = None
    cutoff: date
    source_ending_value_minor: int = Field(
        validation_alias=AliasChoices(
            "source_ending_value_minor", "ending_value_minor", "ending_balance_minor"
        )
    )
    source_records: list[ReconciliationSourceRecordPayload] = Field(default_factory=list)


class ReconciliationApplyPayload(BaseModel):
    client_operation_id: UUID
    balance_adjustment_minor: int | None = None
