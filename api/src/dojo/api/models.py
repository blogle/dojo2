from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

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
    budget_account_id: str
    date: date
    amount_minor: int = Field(gt=0)
    status: TransactionStatus
    memo: str = ""
    fund_shortfall: bool = True
    contribution_category_id: str | None = None


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
    rate_minor: int | None = None
    status: str | None = None
    opening_valuation_minor: int | None = None
    opening_valuation_date: str | None = None


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
    rate_minor: int | None = None
    loan_status: str | None = None


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
    unapplied_credit_minor: int = Field(default=0, ge=0)
    notes: str = ""


class LoanPaymentPayload(BaseModel):
    date: date
    budget_account_id: str
    amount_minor: int = Field(gt=0)
    category_id: str
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
    average_basis_minor: int | None = None


class InvestmentStatementHoldingPayload(BaseModel):
    ticker: str = Field(min_length=1)
    quantity_micros: int = Field(ge=0)
    price_minor: int = Field(gt=0)
    average_basis_minor: int | None = Field(default=None, ge=0)


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
