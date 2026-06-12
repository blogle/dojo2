from __future__ import annotations

from datetime import date
from typing import Literal

from pydantic import BaseModel, Field, model_validator

AccountClass = Literal["BUDGET", "TRACKING_BALANCE", "TRACKING_POSITIONS", "TRACKING_DEBT"]
BudgetAccountType = Literal["DEPOSIT", "CREDIT_CARD"]
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


class AccountPayload(BaseModel):
    name: str = Field(min_length=1)
    account_class: AccountClass
    budget_account_type: BudgetAccountType | None = None
    is_hidden: bool = False
    is_active: bool = True
    display_liability_positive: bool | None = None


class AccountUpdatePayload(BaseModel):
    name: str | None = None
    is_hidden: bool | None = None
    is_active: bool | None = None


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


class CategoryUpdatePayload(BaseModel):
    group_id: str | None = None
    name: str | None = None
    sort_order: int | None = None
    is_hidden: bool | None = None
    is_active: bool | None = None
    target_amount_minor: int | None = None
    due_date_rule: str | None = None
