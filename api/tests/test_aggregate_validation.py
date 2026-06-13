from __future__ import annotations

from dojo.service import DojoService


def _find_check(
    checks: list[dict[str, object]], label: str, entity_name: str, month: str | None = None
) -> dict[str, object]:
    return next(
        check
        for check in checks
        if check["label"] == label
        and check["entity_name"] == entity_name
        and check.get("month") == month
    )


def test_import_validation_report_is_structured_and_passing(service: DojoService) -> None:
    result = service.import_sheet_data(source="fixture://default", source_kind="fixture")

    assert result["ok"] is True
    report = result["validation_report"]
    assert report["passed"] is True
    assert report["summary"]["failed_check_count"] == 0

    checking_actual = _find_check(report["checks"], "account.actual", "Checking")
    atb = _find_check(report["checks"], "budget.available_to_budget", "2026-01", "2026-01")
    assert checking_actual["expected_minor"] == 474000
    assert checking_actual["actual_minor"] == 474000
    assert checking_actual["absolute_delta_minor"] == 0
    assert checking_actual["source_reference"] == [
        "trx_Dates",
        "trx_Outflows",
        "trx_Inflows",
        "trx_Accounts",
        "trx_Statuses",
    ]
    assert atb["expected_minor"] == 424000
    assert atb["actual_minor"] == 424000
    assert "Dashboard!J3" in atb["source_reference"]
    assert "Calculations!B59" in atb["source_reference"]


def test_validation_report_tracks_hidden_budget_summary_semantics(service: DojoService) -> None:
    report = service.import_sheet_data(source="fixture://default", source_kind="fixture")[
        "validation_report"
    ]

    visible_spent = _find_check(report["checks"], "budget.summary.spent", "2026-01", "2026-01")
    hidden_spent = _find_check(
        report["checks"], "budget.summary_with_hidden.spent", "2026-01", "2026-01"
    )
    hidden_category = _find_check(
        report["checks"], "category.visible_budget_membership", "Secret Stash", "2026-01"
    )

    assert visible_spent["expected_minor"] == 15000
    assert visible_spent["actual_minor"] == 15000
    assert hidden_spent["expected_minor"] == 19000
    assert hidden_spent["actual_minor"] == 19000
    assert hidden_category["expected_value"] is False
    assert hidden_category["actual_value"] is False


def test_validation_report_documents_ignored_budget_net_worth_values(service: DojoService) -> None:
    report = service.import_sheet_data(source="fixture://default", source_kind="fixture")[
        "validation_report"
    ]

    ignored_value = _find_check(
        report["checks"], "net_worth.ignored_budget_import_value", "Checking"
    )
    ignored_flag = _find_check(report["checks"], "net_worth.ignored_budget_import_flag", "Checking")
    native_total = _find_check(report["checks"], "net_worth.total", "current")

    assert ignored_value["expected_minor"] == 474000
    assert ignored_value["actual_minor"] == 474000
    assert ignored_flag["expected_value"] is True
    assert ignored_flag["actual_value"] is True
    assert native_total["actual_minor"] == 49469000


def test_validation_report_requires_labeled_ledger_net_worth_rows(service: DojoService) -> None:
    report = service.import_sheet_data(source="fixture://default", source_kind="fixture")[
        "validation_report"
    ]

    labels_present = _find_check(report["checks"], "net_worth.ledger_labels_present", "ledger_rows")
    assert labels_present["expected_value"] == labels_present["actual_value"]
