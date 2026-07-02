"""Eval fixture: proposed patch with raw string-programming in service logic."""

from fastapi import APIRouter

router = APIRouter()


@router.post("/transactions/{transaction_id}/status")
def update_transaction_status(transaction_id: str, status: str) -> dict[str, str]:
    service = TransactionService()
    return service.update_status(transaction_id, status)


class TransactionService:
    def update_status(self, transaction_id: str, status: str) -> dict[str, str]:
        if status == "cleared":
            next_status = "cleared"
        elif status == "pending":
            next_status = "pending"
        else:
            raise ValueError("invalid status")

        save_status(transaction_id, next_status)
        return {"id": transaction_id, "status": next_status}
