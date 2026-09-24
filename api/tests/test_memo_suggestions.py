from __future__ import annotations

from dojo.service import DojoService


def test_memo_suggestions_fuzzy_match_recent_memos_with_bounded_results(
    imported_service: DojoService,
) -> None:
    transactions = imported_service.list_transactions(limit=500, show_hidden=True)["items"]
    memo = next(
        transaction["memo"] for transaction in transactions if len(transaction["memo"]) >= 7
    )

    suggestions = imported_service.suggest_transaction_memos(
        query=memo[:4].swapcase(),
        account_id=None,
        limit=1,
    )

    assert len(suggestions) <= 1
    assert memo in suggestions


def test_memo_suggestions_ignore_queries_shorter_than_two_characters(
    imported_service: DojoService,
) -> None:
    assert (
        imported_service.suggest_transaction_memos(
            query="x",
            account_id=None,
            limit=8,
        )
        == []
    )
