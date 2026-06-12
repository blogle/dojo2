from __future__ import annotations

from collections import defaultdict
from datetime import date, datetime
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid4, uuid5

from dojo.aggregate_validation import build_validation_report
from dojo.constants import (
    ACCOUNT_CLASS_BUDGET,
    ACCOUNT_CLASS_TRACKING_BALANCE,
    BUCKET_TYPE_ATB,
    BUCKET_TYPE_CATEGORY,
    BUDGET_ACCOUNT_TYPE_CREDIT_CARD,
    BUDGET_ACCOUNT_TYPE_DEPOSIT,
    CATEGORY_KIND_CREDIT_CARD_PAYMENT,
    CATEGORY_KIND_STANDARD,
    MAX_TS,
    STATUS_CLEARED,
    SYSTEM_ATB_BUCKET_ID,
    SYSTEM_CATEGORY_ATB,
    SYSTEM_CATEGORY_BALANCE_ADJUSTMENT,
    SYSTEM_CATEGORY_STARTING_BALANCE,
    SYSTEM_CATEGORY_TRANSFER,
    SYSTEM_CREDIT_CARD_GROUP_ID,
)
from dojo.database import Database, json_dumps
from dojo.importer import (
    ParsedImportBundle,
    extract_sheet_id,
    fixture_bundle,
    parse_named_range_workbook,
)
from dojo.scd import close_current_version, insert_version, replace_current_version, utc_now


class ImportValidationError(Exception):
    def __init__(self, report: dict[str, Any]) -> None:
        super().__init__("Import validation failed")
        self.report = report


class DojoService:
    def __init__(self, duckdb_path: str) -> None:
        self.db = Database(duckdb_path)
        self._ensure_system_rows()

    def close(self) -> None:
        self.db.close()

    def _ensure_system_rows(self) -> None:
        now = utc_now()
        with self.db.transaction() as connection:
            group_count_row = connection.execute(
                f"SELECT COUNT(*) FROM current_category_groups WHERE group_id = '{SYSTEM_CREDIT_CARD_GROUP_ID}'"
            ).fetchone()
            if group_count_row is not None and group_count_row[0] == 0:
                insert_version(
                    connection,
                    "category_groups",
                    {
                        "group_id": str(SYSTEM_CREDIT_CARD_GROUP_ID),
                        "name": "Credit Card Payments",
                        "sort_order": 9999,
                        "is_system": True,
                        "is_deletable": False,
                        "is_hidden": False,
                        "valid_from": now,
                        "valid_to": MAX_TS,
                        "created_at": now,
                        "created_by_user_id": None,
                    },
                )
            bucket_count_row = connection.execute(
                f"SELECT COUNT(*) FROM current_budget_buckets WHERE bucket_id = '{SYSTEM_ATB_BUCKET_ID}'"
            ).fetchone()
            if bucket_count_row is not None and bucket_count_row[0] == 0:
                insert_version(
                    connection,
                    "budget_buckets",
                    {
                        "bucket_id": str(SYSTEM_ATB_BUCKET_ID),
                        "bucket_type": BUCKET_TYPE_ATB,
                        "category_id": None,
                        "is_allocatable": True,
                        "is_deletable": False,
                        "valid_from": now,
                        "valid_to": MAX_TS,
                        "created_at": now,
                        "created_by_user_id": None,
                    },
                )

    def get_app_status(self) -> dict[str, Any]:
        latest_batch = self.db.fetch_one(
            "SELECT * FROM import_batches ORDER BY imported_at DESC LIMIT 1"
        )
        latest_run = self.get_import_status()
        return {
            "app": "dojo",
            "ready": latest_batch is not None,
            "mode": "ready" if latest_batch else "onboarding",
            "needs_onboarding": latest_batch is None,
            "latest_import_batch": latest_batch,
            "latest_import_run": latest_run,
        }

    def get_import_status(self) -> dict[str, Any] | None:
        row = self.db.fetch_one("SELECT * FROM import_runs ORDER BY started_at DESC LIMIT 1")
        if row is None:
            return None
        return self._decode_json_fields(row, {"summary", "validation_report"})

    def get_bootstrap(self) -> dict[str, Any]:
        month = self.default_budget_month()
        budget = self.get_budget(month, show_hidden=False)
        return {
            "app_status": self.get_app_status(),
            "import_status": self.get_import_status(),
            "accounts": self.list_accounts(show_hidden=True),
            "category_groups": self.list_category_groups(month=month, show_hidden=True),
            "categories": self.list_categories(month=month, show_hidden=True),
            "budget_buckets": self.db.fetch_all(
                "SELECT * FROM current_budget_buckets ORDER BY bucket_type, category_id"
            ),
            "current_atb_minor": budget["available_to_budget_minor"],
            "current_budget_month_summary": budget["summary"],
            "recent_transactions": self.list_transactions(limit=20, show_hidden=True),
        }

    def default_budget_month(self) -> str:
        return date.today().strftime("%Y-%m")

    def import_sheet_data(
        self,
        *,
        source: str,
        source_kind: str,
        spreadsheet_title: str | None = None,
        named_ranges: dict[str, list[list[str]]] | None = None,
        available_named_ranges: list[str] | None = None,
        expected: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        started_at = utc_now()
        import_run_id = str(uuid4())
        spreadsheet_id = extract_sheet_id(source)
        try:
            if source_kind == "fixture":
                bundle = fixture_bundle()
            else:
                if named_ranges is None or spreadsheet_title is None:
                    raise ValueError("Live import requires named range data")
                bundle = parse_named_range_workbook(
                    spreadsheet_id=spreadsheet_id,
                    spreadsheet_title=spreadsheet_title,
                    named_ranges=named_ranges,
                    source_kind=source_kind,
                    expected=expected,
                    available_named_ranges=available_named_ranges,
                )
            validation_report = self._apply_import_bundle(bundle)
        except ImportValidationError as exc:
            self._record_import_run(
                import_run_id=import_run_id,
                spreadsheet_id=spreadsheet_id,
                spreadsheet_title=spreadsheet_title or source,
                started_at=started_at,
                completed_at=utc_now(),
                status="failed",
                source_kind=source_kind,
                validation_passed=False,
                summary={
                    "hard_failures": len(exc.report["hard_failures"]),
                    "warnings": len(exc.report["warnings"]),
                },
                validation_report=exc.report,
                error_message="validation failed",
            )
            return {
                "ok": False,
                "validation_report": exc.report,
                "import_status": self.get_import_status(),
            }
        except Exception as exc:
            self._record_import_run(
                import_run_id=import_run_id,
                spreadsheet_id=spreadsheet_id,
                spreadsheet_title=spreadsheet_title or source,
                started_at=started_at,
                completed_at=utc_now(),
                status="failed",
                source_kind=source_kind,
                validation_passed=False,
                summary=None,
                validation_report=None,
                error_message=str(exc),
            )
            raise

        self._record_import_run(
            import_run_id=import_run_id,
            spreadsheet_id=bundle.spreadsheet_id,
            spreadsheet_title=bundle.spreadsheet_title,
            started_at=started_at,
            completed_at=utc_now(),
            status="succeeded",
            source_kind=source_kind,
            validation_passed=True,
            summary=validation_report["summary"],
            validation_report=validation_report,
            error_message=None,
        )
        return {
            "ok": True,
            "import_batch": self.db.fetch_one(
                "SELECT * FROM import_batches ORDER BY imported_at DESC LIMIT 1"
            ),
            "validation_report": validation_report,
            "app_status": self.get_app_status(),
        }

    def _apply_import_bundle(self, bundle: ParsedImportBundle) -> dict[str, Any]:
        imported_at = utc_now()
        with self.db.transaction() as connection:
            self._clear_domain_tables(connection)
            self._insert_bundle(connection, bundle, imported_at)
            report = self._validate_bundle(bundle)
            if report["hard_failures"]:
                raise ImportValidationError(report)
            connection.execute(
                "INSERT INTO import_batches (import_batch_id, spreadsheet_id, spreadsheet_title, imported_at, cutover_at, summary) VALUES (?, ?, ?, ?, ?, CAST(? AS JSON))",
                (
                    str(uuid4()),
                    bundle.spreadsheet_id,
                    bundle.spreadsheet_title,
                    imported_at,
                    imported_at,
                    json_dumps(report["summary"]),
                ),
            )
        return report

    def _clear_domain_tables(self, connection: Any) -> None:
        for table in (
            "net_worth_valuations",
            "allocations",
            "transactions",
            "budget_buckets",
            "categories",
            "category_groups",
            "budget_account_settings",
            "accounts",
            "import_batches",
        ):
            connection.execute(f"DELETE FROM {table}")

    def _insert_bundle(
        self, connection: Any, bundle: ParsedImportBundle, imported_at: datetime
    ) -> None:
        group_by_name = {group.name: group for group in bundle.groups}
        category_by_name = {category.name: category for category in bundle.categories}
        account_ids_by_name = {account.name: account.account_id for account in bundle.accounts}

        for group in bundle.groups:
            group_id = (
                str(SYSTEM_CREDIT_CARD_GROUP_ID)
                if group.is_system and group.name == "Credit Card Payments"
                else group.group_id
            )
            insert_version(
                connection,
                "category_groups",
                {
                    "group_id": group_id,
                    "name": group.name,
                    "sort_order": group.sort_order,
                    "is_system": group.is_system,
                    "is_deletable": group.is_deletable,
                    "is_hidden": group.is_hidden,
                    "valid_from": imported_at,
                    "valid_to": MAX_TS,
                    "created_at": imported_at,
                    "created_by_user_id": None,
                },
            )

        insert_version(
            connection,
            "budget_buckets",
            {
                "bucket_id": str(SYSTEM_ATB_BUCKET_ID),
                "bucket_type": BUCKET_TYPE_ATB,
                "category_id": None,
                "is_allocatable": True,
                "is_deletable": False,
                "valid_from": imported_at,
                "valid_to": MAX_TS,
                "created_at": imported_at,
                "created_by_user_id": None,
            },
        )

        for account in bundle.accounts:
            insert_version(
                connection,
                "accounts",
                {
                    "account_id": account.account_id,
                    "account_class": account.account_class,
                    "name": account.name,
                    "is_hidden": account.is_hidden,
                    "is_active": account.is_active,
                    "metadata": json_dumps({}),
                    "valid_from": imported_at,
                    "valid_to": MAX_TS,
                    "created_at": imported_at,
                    "created_by_user_id": None,
                },
            )

        for category in bundle.categories:
            group = group_by_name[category.group_name]
            group_id = (
                str(SYSTEM_CREDIT_CARD_GROUP_ID)
                if group.is_system and group.name == "Credit Card Payments"
                else group.group_id
            )
            insert_version(
                connection,
                "categories",
                {
                    "category_id": category.category_id,
                    "group_id": group_id,
                    "name": category.name,
                    "category_kind": category.category_kind,
                    "sort_order": category.sort_order,
                    "is_hidden": category.is_hidden,
                    "is_active": category.is_active,
                    "target_amount_minor": category.target_amount_minor,
                    "due_date_rule": category.due_date_rule,
                    "metadata": json_dumps({"linked_account_name": category.linked_account_name}),
                    "valid_from": imported_at,
                    "valid_to": MAX_TS,
                    "created_at": imported_at,
                    "created_by_user_id": None,
                },
            )
            insert_version(
                connection,
                "budget_buckets",
                {
                    "bucket_id": self._bucket_id_for_category(category.category_id),
                    "bucket_type": BUCKET_TYPE_CATEGORY,
                    "category_id": category.category_id,
                    "is_allocatable": True,
                    "is_deletable": category.category_kind != CATEGORY_KIND_CREDIT_CARD_PAYMENT,
                    "valid_from": imported_at,
                    "valid_to": MAX_TS,
                    "created_at": imported_at,
                    "created_by_user_id": None,
                },
            )

        for account in bundle.accounts:
            if account.account_class != ACCOUNT_CLASS_BUDGET or account.budget_account_type is None:
                continue
            linked_payment_category_id = None
            if account.linked_payment_category_name:
                linked_payment_category_id = category_by_name[
                    account.linked_payment_category_name
                ].category_id
            insert_version(
                connection,
                "budget_account_settings",
                {
                    "account_id": account.account_id,
                    "budget_account_type": account.budget_account_type,
                    "linked_payment_category_id": linked_payment_category_id,
                    "display_liability_positive": account.display_liability_positive,
                    "valid_from": imported_at,
                    "valid_to": MAX_TS,
                    "created_at": imported_at,
                    "created_by_user_id": None,
                },
            )

        for transaction in bundle.transactions:
            transaction_account_id = account_ids_by_name[transaction.account_name]
            category_id = (
                category_by_name[transaction.category_name].category_id
                if transaction.category_name
                else None
            )
            insert_version(
                connection,
                "transactions",
                {
                    "transaction_id": transaction.transaction_id,
                    "date": transaction.date,
                    "account_id": transaction_account_id,
                    "amount_minor": transaction.amount_minor,
                    "category_id": category_id,
                    "system_category": transaction.system_category,
                    "status": transaction.status,
                    "memo": transaction.memo,
                    "valid_from": imported_at,
                    "valid_to": MAX_TS,
                    "created_at": imported_at,
                    "created_by_user_id": None,
                },
            )

        for allocation in bundle.allocations:
            insert_version(
                connection,
                "allocations",
                {
                    "allocation_id": allocation.allocation_id,
                    "date": allocation.date,
                    "from_bucket_id": self._bucket_id_from_name(
                        allocation.from_name, category_by_name
                    ),
                    "to_bucket_id": self._bucket_id_from_name(allocation.to_name, category_by_name),
                    "amount_minor": allocation.amount_minor,
                    "memo": allocation.memo,
                    "valid_from": imported_at,
                    "valid_to": MAX_TS,
                    "created_at": imported_at,
                    "created_by_user_id": None,
                },
            )

        for valuation in bundle.valuations:
            account_id: str | None = None
            if valuation.account_name is not None:
                account_id = account_ids_by_name[valuation.account_name]
            elif valuation.raw_name not in account_ids_by_name:
                new_account_id = self._tracking_account_id(valuation.raw_name)
                account_ids_by_name[valuation.raw_name] = new_account_id
                insert_version(
                    connection,
                    "accounts",
                    {
                        "account_id": new_account_id,
                        "account_class": ACCOUNT_CLASS_TRACKING_BALANCE,
                        "name": valuation.raw_name,
                        "is_hidden": False,
                        "is_active": True,
                        "metadata": json_dumps(
                            {
                                "imported_from_net_worth": True,
                                "net_worth_match_kind": valuation.match_kind,
                                "net_worth_match_candidates": list(valuation.match_candidates),
                            }
                        ),
                        "valid_from": imported_at,
                        "valid_to": MAX_TS,
                        "created_at": imported_at,
                        "created_by_user_id": None,
                    },
                )
                account_id = new_account_id
            else:
                account_id = account_ids_by_name[valuation.raw_name]

            insert_version(
                connection,
                "net_worth_valuations",
                {
                    "valuation_id": valuation.valuation_id,
                    "account_id": account_id,
                    "raw_name": valuation.raw_name,
                    "effective_date": valuation.effective_date,
                    "amount_minor": valuation.amount_minor,
                    "notes": valuation.notes,
                    "metadata": json_dumps(
                        {
                            "normalized_name": valuation.normalized_name,
                            "match_kind": valuation.match_kind,
                            "match_candidates": list(valuation.match_candidates),
                        }
                    ),
                    "valid_from": imported_at,
                    "valid_to": MAX_TS,
                    "created_at": imported_at,
                    "created_by_user_id": None,
                },
            )

    def _validate_bundle(self, bundle: ParsedImportBundle) -> dict[str, Any]:
        return build_validation_report(self, bundle)

    def snapshot_for_validation(self, months: list[str]) -> dict[str, Any]:
        account_balances = {
            account["name"]: {
                "actual": account["actual_balance_minor"],
                "pending": account["pending_balance_minor"],
                "cleared": account["cleared_balance_minor"],
            }
            for account in self.list_accounts(show_hidden=True)
            if account["account_class"] == ACCOUNT_CLASS_BUDGET
        }
        category_available = {
            category["name"]: category["available_minor"]
            for category in self.list_categories(
                month=self.default_budget_month(), show_hidden=True
            )
        }
        month_activity: dict[str, dict[str, int]] = {}
        month_budgeted: dict[str, dict[str, int]] = {}
        starting_available: dict[str, dict[str, int]] = {}
        for month in months:
            categories = self.list_categories(month=month, show_hidden=True)
            month_activity[month] = {
                category["name"]: category["month_activity_minor"] for category in categories
            }
            month_budgeted[month] = {
                category["name"]: category["month_budgeted_minor"] for category in categories
            }
            starting_available[month] = {
                category["name"]: category["starting_available_minor"] for category in categories
            }
        return {
            "account_count": len(self.list_accounts(show_hidden=True)),
            "category_group_count": len(
                self.list_category_groups(month=self.default_budget_month(), show_hidden=True)
            ),
            "category_count": len(
                self.list_categories(month=self.default_budget_month(), show_hidden=True)
            ),
            "net_worth_valuation_rows": len(
                self.db.fetch_all("SELECT * FROM current_net_worth_valuations")
            ),
            "account_balances": account_balances,
            "atb_available_minor": self.compute_available_to_budget(),
            "category_available": category_available,
            "month_activity": month_activity,
            "month_budgeted": month_budgeted,
            "starting_available": starting_available,
            "native_net_worth_minor": self.get_net_worth()["current_net_worth_minor"],
        }

    def _check_equal(
        self,
        checks: list[dict[str, Any]],
        hard_failures: list[dict[str, Any]],
        label: str,
        actual: Any,
        expected: Any,
    ) -> None:
        check = {
            "label": label,
            "actual": actual,
            "expected": expected,
            "passed": actual == expected,
        }
        checks.append(check)
        if actual != expected:
            hard_failures.append(check)

    def _record_import_run(
        self,
        *,
        import_run_id: str,
        spreadsheet_id: str,
        spreadsheet_title: str,
        started_at: datetime,
        completed_at: datetime,
        status: str,
        source_kind: str,
        validation_passed: bool,
        summary: dict[str, Any] | None,
        validation_report: dict[str, Any] | None,
        error_message: str | None,
    ) -> None:
        self.db.execute(
            "INSERT INTO import_runs (import_run_id, spreadsheet_id, spreadsheet_title, started_at, completed_at, status, source_kind, validation_passed, summary, validation_report, error_message) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CAST(? AS JSON), CAST(? AS JSON), ?)",
            (
                import_run_id,
                spreadsheet_id,
                spreadsheet_title,
                started_at,
                completed_at,
                status,
                source_kind,
                validation_passed,
                json_dumps(summary),
                json_dumps(validation_report),
                error_message,
            ),
        )

    def list_accounts(self, *, show_hidden: bool) -> list[dict[str, Any]]:
        accounts = self.db.fetch_all(
            """
            SELECT a.*, s.budget_account_type, s.linked_payment_category_id, s.display_liability_positive
            FROM current_accounts a
            LEFT JOIN current_budget_account_settings s ON s.account_id = a.account_id
            ORDER BY a.name
            """
        )
        balances = self._account_balances()
        results = []
        for account in accounts:
            if account["is_hidden"] and not show_hidden:
                continue
            account_balances = balances.get(
                account["account_id"], {"actual": 0, "pending": 0, "cleared": 0}
            )
            display_balance = account_balances["actual"]
            if account.get(
                "budget_account_type"
            ) == BUDGET_ACCOUNT_TYPE_CREDIT_CARD and account.get("display_liability_positive"):
                display_balance = -display_balance
            results.append(
                account
                | {
                    "actual_balance_minor": account_balances["actual"],
                    "pending_balance_minor": account_balances["pending"],
                    "cleared_balance_minor": account_balances["cleared"],
                    "display_balance_minor": display_balance,
                }
            )
        return results

    def list_transactions(self, *, limit: int, show_hidden: bool) -> list[dict[str, Any]]:
        accounts = {
            row["account_id"]: row for row in self.db.fetch_all("SELECT * FROM current_accounts")
        }
        categories = {
            row["category_id"]: row for row in self.db.fetch_all("SELECT * FROM current_categories")
        }
        rows = self.db.fetch_all(
            "SELECT * FROM current_transactions ORDER BY date DESC, created_at DESC, transaction_id DESC"
        )
        results: list[dict[str, Any]] = []
        for row in rows:
            account = accounts[row["account_id"]]
            category = categories.get(row["category_id"])
            hidden = account["is_hidden"] or (category["is_hidden"] if category else False)
            if hidden and not show_hidden:
                continue
            results.append(
                row
                | {
                    "account_name": account["name"],
                    "category_name": category["name"] if category else None,
                    "is_hidden_entity": hidden,
                }
            )
        return results[:limit]

    def list_category_groups(self, *, month: str, show_hidden: bool) -> list[dict[str, Any]]:
        groups = self.db.fetch_all(
            "SELECT * FROM current_category_groups ORDER BY sort_order, name"
        )
        categories = self.list_categories(month=month, show_hidden=True)
        categories_by_group: dict[Any, list[dict[str, Any]]] = defaultdict(list)
        for category in categories:
            categories_by_group[category["group_id"]].append(category)
        results = []
        for group in groups:
            visible_categories = [
                category
                for category in categories_by_group[group["group_id"]]
                if show_hidden or not category["is_hidden"]
            ]
            if group["is_hidden"] and not show_hidden and not visible_categories:
                continue
            results.append(
                group
                | {
                    "categories": visible_categories,
                    "totals": {
                        "available_minor": sum(
                            category["available_minor"] for category in visible_categories
                        ),
                        "month_activity_minor": sum(
                            category["month_activity_minor"] for category in visible_categories
                        ),
                        "month_budgeted_minor": sum(
                            category["month_budgeted_minor"] for category in visible_categories
                        ),
                        "starting_available_minor": sum(
                            category["starting_available_minor"] for category in visible_categories
                        ),
                    },
                }
            )
        return results

    def list_categories(self, *, month: str, show_hidden: bool) -> list[dict[str, Any]]:
        categories = self.db.fetch_all("SELECT * FROM current_categories ORDER BY sort_order, name")
        groups = {
            row["group_id"]: row
            for row in self.db.fetch_all("SELECT * FROM current_category_groups")
        }
        settings = {
            row["linked_payment_category_id"]: row
            for row in self.db.fetch_all("SELECT * FROM current_budget_account_settings")
            if row["linked_payment_category_id"] is not None
        }
        month_start, month_end = self._month_bounds(month)
        results = []
        for category in categories:
            if category["is_hidden"] and not show_hidden:
                continue
            bucket_id = self._bucket_id_for_category(category["category_id"])
            available = self.compute_category_available(category["category_id"])
            results.append(
                category
                | {
                    "bucket_id": bucket_id,
                    "group_name": groups[category["group_id"]]["name"],
                    "available_minor": available,
                    "month_activity_minor": self.compute_month_activity(
                        category["category_id"], month_start, month_end
                    ),
                    "month_budgeted_minor": self.compute_month_budgeted(
                        bucket_id, month_start, month_end
                    ),
                    "starting_available_minor": self.compute_carried_over(
                        category["category_id"], bucket_id, month_start
                    ),
                    "linked_account_id": settings.get(category["category_id"], {}).get(
                        "account_id"
                    ),
                }
            )
        return sorted(
            results,
            key=lambda item: (
                groups[item["group_id"]]["sort_order"],
                item["sort_order"],
                item["name"],
            ),
        )

    def get_budget(self, month: str, *, show_hidden: bool) -> dict[str, Any]:
        categories = self.list_categories(month=month, show_hidden=show_hidden)
        month_start, month_end = self._month_bounds(month)
        visible_standard = [
            category
            for category in categories
            if category["category_kind"] == CATEGORY_KIND_STANDARD
        ]
        return {
            "month": month,
            "available_to_budget_minor": self.compute_available_to_budget(),
            "summary": {
                "month_activity_minor": sum(
                    category["month_activity_minor"] for category in visible_standard
                ),
                "month_budgeted_minor": sum(
                    category["month_budgeted_minor"] for category in visible_standard
                ),
                "starting_available_minor": sum(
                    category["starting_available_minor"] for category in visible_standard
                ),
                "reportable_income_minor": self.compute_reportable_income(month_start, month_end),
                "spent_minor": self.compute_spent(month_start, month_end, show_hidden=show_hidden),
            },
            "groups": self.list_category_groups(month=month, show_hidden=show_hidden),
        }

    def get_net_worth(self) -> dict[str, Any]:
        accounts = {
            row["account_id"]: row for row in self.db.fetch_all("SELECT * FROM current_accounts")
        }
        valuations = [
            self._decode_json_fields(row, {"metadata"})
            for row in self.db.fetch_all(
            "SELECT * FROM current_net_worth_valuations ORDER BY effective_date DESC, created_at DESC"
            )
        ]
        latest_valuation_by_account: dict[str, dict[str, Any]] = {}
        for valuation in valuations:
            account_id = valuation["account_id"] or valuation["raw_name"]
            latest_valuation_by_account.setdefault(account_id, valuation)

        total = 0
        items = []
        for account in self.list_accounts(show_hidden=True):
            if account["account_class"] == ACCOUNT_CLASS_BUDGET:
                amount = account["actual_balance_minor"]
                total += amount
                items.append(
                    account
                    | {
                        "account_name": account["name"],
                        "net_worth_minor": amount,
                        "source": "ledger",
                        "ignored_import_value": False,
                        "ignored_reason": None,
                        "match_candidates": [],
                    }
                )

        for valuation in latest_valuation_by_account.values():
            account_row = accounts.get(cast(str, valuation["account_id"]))
            if account_row is None:
                continue
            metadata = cast(dict[str, Any], valuation.get("metadata") or {})
            account_name = account_row["name"] if account_row else valuation["raw_name"]
            if metadata.get("match_kind") == "AMBIGUOUS_BUDGET_ACCOUNT":
                items.append(
                    valuation
                    | {
                        "account_name": account_name,
                        "net_worth_minor": valuation["amount_minor"],
                        "source": "imported_valuation",
                        "ignored_import_value": True,
                        "ignored_reason": "ambiguous_budget_duplicate",
                        "match_candidates": metadata.get("match_candidates", []),
                    }
                )
                continue
            if account_row["account_class"] == ACCOUNT_CLASS_BUDGET:
                items.append(
                    valuation
                    | {
                        "account_name": account_name,
                        "net_worth_minor": valuation["amount_minor"],
                        "source": "imported_valuation",
                        "ignored_import_value": True,
                        "ignored_reason": "duplicate_budget_account",
                        "match_candidates": metadata.get("match_candidates", []),
                    }
                )
                continue
            total += valuation["amount_minor"]
            items.append(
                valuation
                | {
                    "account_name": account_name,
                    "net_worth_minor": valuation["amount_minor"],
                    "source": "imported_valuation",
                    "ignored_import_value": False,
                    "ignored_reason": None,
                    "match_candidates": metadata.get("match_candidates", []),
                }
            )
        return {"current_net_worth_minor": total, "items": items}

    def create_allocation(
        self,
        *,
        from_bucket_id: str,
        to_bucket_id: str,
        amount_minor: int,
        memo: str,
        allocation_date: date,
    ) -> dict[str, Any]:
        if amount_minor <= 0:
            raise ValueError("Allocation amount must be positive")
        now = utc_now()
        allocation_id = str(uuid4())
        with self.db.transaction() as connection:
            insert_version(
                connection,
                "allocations",
                {
                    "allocation_id": allocation_id,
                    "date": allocation_date,
                    "from_bucket_id": from_bucket_id,
                    "to_bucket_id": to_bucket_id,
                    "amount_minor": amount_minor,
                    "memo": memo,
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
        return {"allocation_id": allocation_id}

    def create_transaction(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        transaction_id = str(uuid4())
        self._validate_transaction_payload(payload)
        with self.db.transaction() as connection:
            insert_version(
                connection,
                "transactions",
                {
                    "transaction_id": transaction_id,
                    "date": payload["date"],
                    "account_id": payload["account_id"],
                    "amount_minor": payload["amount_minor"],
                    "category_id": payload.get("category_id"),
                    "system_category": payload.get("system_category"),
                    "status": payload["status"],
                    "memo": payload.get("memo", ""),
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
        return {"transaction_id": transaction_id}

    def update_transaction(self, transaction_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._validate_transaction_payload(payload)
        current = self.db.fetch_one(
            "SELECT * FROM current_transactions WHERE transaction_id = ?",
            (transaction_id,),
        )
        if current is None:
            raise ValueError("Transaction not found")
        now = utc_now()
        with self.db.transaction() as connection:
            replace_current_version(
                connection,
                "transactions",
                "transaction_id",
                transaction_id,
                {
                    "row_id": str(uuid4()),
                    "transaction_id": transaction_id,
                    "date": payload["date"],
                    "account_id": payload["account_id"],
                    "amount_minor": payload["amount_minor"],
                    "category_id": payload.get("category_id"),
                    "system_category": payload.get("system_category"),
                    "status": payload["status"],
                    "memo": payload.get("memo", ""),
                    "created_at": current["created_at"],
                    "created_by_user_id": None,
                },
                now=now,
            )
        return {"transaction_id": transaction_id}

    def delete_transaction(self, transaction_id: str) -> None:
        with self.db.transaction() as connection:
            close_current_version(connection, "transactions", "transaction_id", transaction_id)

    def create_transfer(
        self,
        *,
        from_account_id: str,
        to_account_id: str,
        amount_minor: int,
        transfer_date: date,
        memo: str,
        status: str,
    ) -> dict[str, Any]:
        if amount_minor <= 0:
            raise ValueError("Transfer amount must be positive")
        now = utc_now()
        source_transaction_id = str(uuid4())
        destination_transaction_id = str(uuid4())
        with self.db.transaction() as connection:
            for transaction_id, account_id, signed_amount in (
                (source_transaction_id, from_account_id, -amount_minor),
                (destination_transaction_id, to_account_id, amount_minor),
            ):
                insert_version(
                    connection,
                    "transactions",
                    {
                        "transaction_id": transaction_id,
                        "date": transfer_date,
                        "account_id": account_id,
                        "amount_minor": signed_amount,
                        "category_id": None,
                        "system_category": SYSTEM_CATEGORY_TRANSFER,
                        "status": status,
                        "memo": memo,
                        "valid_from": now,
                        "valid_to": MAX_TS,
                        "created_at": now,
                        "created_by_user_id": None,
                    },
                )
        return {
            "source_transaction_id": source_transaction_id,
            "destination_transaction_id": destination_transaction_id,
        }

    def create_account(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        account_id = str(uuid4())
        with self.db.transaction() as connection:
            insert_version(
                connection,
                "accounts",
                {
                    "account_id": account_id,
                    "account_class": payload["account_class"],
                    "name": payload["name"],
                    "is_hidden": payload.get("is_hidden", False),
                    "is_active": payload.get("is_active", True),
                    "metadata": json_dumps({}),
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
            if payload["account_class"] == ACCOUNT_CLASS_BUDGET:
                budget_account_type = payload.get(
                    "budget_account_type", BUDGET_ACCOUNT_TYPE_DEPOSIT
                )
                linked_payment_category_id = None
                if budget_account_type == BUDGET_ACCOUNT_TYPE_CREDIT_CARD:
                    linked_payment_category_id = self._create_credit_card_payment_category(
                        connection, payload["name"], now
                    )
                insert_version(
                    connection,
                    "budget_account_settings",
                    {
                        "account_id": account_id,
                        "budget_account_type": budget_account_type,
                        "linked_payment_category_id": linked_payment_category_id,
                        "display_liability_positive": payload.get(
                            "display_liability_positive",
                            budget_account_type == BUDGET_ACCOUNT_TYPE_CREDIT_CARD,
                        ),
                        "valid_from": now,
                        "valid_to": MAX_TS,
                        "created_at": now,
                        "created_by_user_id": None,
                    },
                )
        return {"account_id": account_id}

    def update_account(self, account_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.db.fetch_one(
            "SELECT * FROM current_accounts WHERE account_id = ?", (account_id,)
        )
        if current is None:
            raise ValueError("Account not found")
        now = utc_now()
        with self.db.transaction() as connection:
            replace_current_version(
                connection,
                "accounts",
                "account_id",
                account_id,
                {
                    "row_id": str(uuid4()),
                    "account_id": account_id,
                    "account_class": current["account_class"],
                    "name": payload.get("name", current["name"]),
                    "is_hidden": payload.get("is_hidden", current["is_hidden"]),
                    "is_active": payload.get("is_active", current["is_active"]),
                    "metadata": current["metadata"],
                    "created_at": current["created_at"],
                    "created_by_user_id": current["created_by_user_id"],
                },
                now=now,
            )
        return {"account_id": account_id}

    def create_category_group(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        group_id = str(uuid4())
        insert_values = {
            "group_id": group_id,
            "name": payload["name"],
            "sort_order": payload["sort_order"],
            "is_system": False,
            "is_deletable": True,
            "is_hidden": payload.get("is_hidden", False),
            "valid_from": now,
            "valid_to": MAX_TS,
            "created_at": now,
            "created_by_user_id": None,
        }
        with self.db.transaction() as connection:
            insert_version(connection, "category_groups", insert_values)
        return {"group_id": group_id}

    def update_category_group(self, group_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.db.fetch_one(
            "SELECT * FROM current_category_groups WHERE group_id = ?", (group_id,)
        )
        if current is None:
            raise ValueError("Category group not found")
        now = utc_now()
        with self.db.transaction() as connection:
            replace_current_version(
                connection,
                "category_groups",
                "group_id",
                group_id,
                {
                    "row_id": str(uuid4()),
                    "group_id": group_id,
                    "name": payload.get("name", current["name"]),
                    "sort_order": payload.get("sort_order", current["sort_order"]),
                    "is_system": current["is_system"],
                    "is_deletable": current["is_deletable"],
                    "is_hidden": payload.get("is_hidden", current["is_hidden"]),
                    "created_at": current["created_at"],
                    "created_by_user_id": current["created_by_user_id"],
                },
                now=now,
            )
        return {"group_id": group_id}

    def create_category(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = utc_now()
        category_id = str(uuid4())
        with self.db.transaction() as connection:
            insert_version(
                connection,
                "categories",
                {
                    "category_id": category_id,
                    "group_id": payload["group_id"],
                    "name": payload["name"],
                    "category_kind": payload.get("category_kind", CATEGORY_KIND_STANDARD),
                    "sort_order": payload["sort_order"],
                    "is_hidden": payload.get("is_hidden", False),
                    "is_active": payload.get("is_active", True),
                    "target_amount_minor": payload.get("target_amount_minor"),
                    "due_date_rule": payload.get("due_date_rule"),
                    "metadata": json_dumps({}),
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
            insert_version(
                connection,
                "budget_buckets",
                {
                    "bucket_id": self._bucket_id_for_category(category_id),
                    "bucket_type": BUCKET_TYPE_CATEGORY,
                    "category_id": category_id,
                    "is_allocatable": True,
                    "is_deletable": True,
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
        return {"category_id": category_id}

    def update_category(self, category_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.db.fetch_one(
            "SELECT * FROM current_categories WHERE category_id = ?", (category_id,)
        )
        if current is None:
            raise ValueError("Category not found")
        now = utc_now()
        with self.db.transaction() as connection:
            replace_current_version(
                connection,
                "categories",
                "category_id",
                category_id,
                {
                    "row_id": str(uuid4()),
                    "category_id": category_id,
                    "group_id": payload.get("group_id", current["group_id"]),
                    "name": payload.get("name", current["name"]),
                    "category_kind": current["category_kind"],
                    "sort_order": payload.get("sort_order", current["sort_order"]),
                    "is_hidden": payload.get("is_hidden", current["is_hidden"]),
                    "is_active": payload.get("is_active", current["is_active"]),
                    "target_amount_minor": payload.get(
                        "target_amount_minor", current["target_amount_minor"]
                    ),
                    "due_date_rule": payload.get("due_date_rule", current["due_date_rule"]),
                    "metadata": current["metadata"],
                    "created_at": current["created_at"],
                    "created_by_user_id": current["created_by_user_id"],
                },
                now=now,
            )
        return {"category_id": category_id}

    def compute_available_to_budget(self) -> int:
        transactions = self.db.fetch_all(
            """
            SELECT t.amount_minor, t.system_category
            FROM current_transactions t
            JOIN current_accounts a ON a.account_id = t.account_id
            WHERE a.account_class = ? AND t.system_category IN (?, ?, ?)
            """,
            (
                ACCOUNT_CLASS_BUDGET,
                SYSTEM_CATEGORY_ATB,
                SYSTEM_CATEGORY_STARTING_BALANCE,
                SYSTEM_CATEGORY_BALANCE_ADJUSTMENT,
            ),
        )
        allocations = self.db.fetch_all(
            "SELECT from_bucket_id, to_bucket_id, amount_minor FROM current_allocations"
        )
        total = 0
        for transaction in transactions:
            if transaction["system_category"] == SYSTEM_CATEGORY_STARTING_BALANCE:
                if transaction["amount_minor"] > 0:
                    total += int(transaction["amount_minor"])
                continue
            total += int(transaction["amount_minor"])
        for allocation in allocations:
            if allocation["to_bucket_id"] == str(SYSTEM_ATB_BUCKET_ID):
                total += allocation["amount_minor"]
            if allocation["from_bucket_id"] == str(SYSTEM_ATB_BUCKET_ID):
                total -= allocation["amount_minor"]
        return int(total)

    def compute_category_available(self, category_id: str) -> int:
        category = self.db.fetch_one(
            "SELECT * FROM current_categories WHERE category_id = ?", (category_id,)
        )
        if category is None:
            raise ValueError("Category not found")
        bucket_id = self._bucket_id_for_category(category_id)
        allocations = self.db.fetch_all(
            "SELECT from_bucket_id, to_bucket_id, amount_minor FROM current_allocations"
        )
        transactions = self.db.fetch_all("SELECT * FROM current_transactions")
        if category["category_kind"] == CATEGORY_KIND_STANDARD:
            return self._standard_category_available(
                category_id, bucket_id, transactions, allocations
            )
        return self._credit_card_payment_available(
            category_id, bucket_id, transactions, allocations
        )

    def compute_month_activity(self, category_id: str, month_start: date, month_end: date) -> int:
        transactions = self.db.fetch_all(
            "SELECT amount_minor, date FROM current_transactions WHERE category_id = ?",
            (category_id,),
        )
        return sum(
            transaction["amount_minor"]
            for transaction in transactions
            if month_start <= transaction["date"] <= month_end
        )

    def compute_month_budgeted(self, bucket_id: str, month_start: date, month_end: date) -> int:
        allocations = self.db.fetch_all(
            "SELECT from_bucket_id, to_bucket_id, amount_minor, date FROM current_allocations"
        )
        total = 0
        for allocation in allocations:
            if not month_start <= allocation["date"] <= month_end:
                continue
            if allocation["to_bucket_id"] == bucket_id:
                total += allocation["amount_minor"]
            if allocation["from_bucket_id"] == bucket_id:
                total -= allocation["amount_minor"]
        return total

    def compute_carried_over(self, category_id: str, bucket_id: str, month_start: date) -> int:
        transactions = self.db.fetch_all(
            "SELECT amount_minor, date FROM current_transactions WHERE category_id = ?",
            (category_id,),
        )
        allocations = self.db.fetch_all(
            "SELECT from_bucket_id, to_bucket_id, amount_minor, date FROM current_allocations"
        )
        total = int(
            sum(
                int(transaction["amount_minor"])
                for transaction in transactions
                if transaction["date"] < month_start
            )
        )
        for allocation in allocations:
            if allocation["date"] >= month_start:
                continue
            if allocation["to_bucket_id"] == bucket_id:
                total += allocation["amount_minor"]
            if allocation["from_bucket_id"] == bucket_id:
                total -= allocation["amount_minor"]
        return int(total)

    def compute_reportable_income(self, month_start: date, month_end: date) -> int:
        transactions = self.db.fetch_all(
            "SELECT amount_minor, date FROM current_transactions WHERE system_category = ?",
            (SYSTEM_CATEGORY_ATB,),
        )
        return sum(
            transaction["amount_minor"]
            for transaction in transactions
            if transaction["amount_minor"] > 0 and month_start <= transaction["date"] <= month_end
        )

    def compute_spent(self, month_start: date, month_end: date, *, show_hidden: bool) -> int:
        categories = {
            row["category_id"]: row for row in self.db.fetch_all("SELECT * FROM current_categories")
        }
        transactions = self.db.fetch_all(
            "SELECT amount_minor, date, category_id FROM current_transactions WHERE category_id IS NOT NULL"
        )
        spent = 0
        refunds = 0
        for transaction in transactions:
            category = categories[transaction["category_id"]]
            if category["category_kind"] != CATEGORY_KIND_STANDARD:
                continue
            if category["is_hidden"] and not show_hidden:
                continue
            if not month_start <= transaction["date"] <= month_end:
                continue
            if transaction["amount_minor"] < 0:
                spent += -transaction["amount_minor"]
            else:
                refunds += transaction["amount_minor"]
        return spent - refunds

    def _standard_category_available(
        self,
        category_id: str,
        bucket_id: str,
        transactions: list[dict[str, Any]],
        allocations: list[dict[str, Any]],
    ) -> int:
        total = int(
            sum(
                int(transaction["amount_minor"])
                for transaction in transactions
                if transaction["category_id"] == category_id
            )
        )
        for allocation in allocations:
            if allocation["to_bucket_id"] == bucket_id:
                total += allocation["amount_minor"]
            if allocation["from_bucket_id"] == bucket_id:
                total -= allocation["amount_minor"]
        return int(total)

    def _credit_card_payment_available(
        self,
        category_id: str,
        bucket_id: str,
        transactions: list[dict[str, Any]],
        allocations: list[dict[str, Any]],
    ) -> int:
        setting = self.db.fetch_one(
            "SELECT * FROM current_budget_account_settings WHERE linked_payment_category_id = ?",
            (category_id,),
        )
        if setting is None:
            return 0
        total = 0
        for allocation in allocations:
            if allocation["to_bucket_id"] == bucket_id:
                total += allocation["amount_minor"]
            if allocation["from_bucket_id"] == bucket_id:
                total -= allocation["amount_minor"]
        for transaction in transactions:
            if (
                transaction["account_id"] == setting["account_id"]
                and transaction["category_id"] is not None
            ):
                total += -transaction["amount_minor"]
            if (
                transaction["account_id"] == setting["account_id"]
                and transaction["system_category"] == SYSTEM_CATEGORY_TRANSFER
                and transaction["amount_minor"] > 0
            ):
                total -= transaction["amount_minor"]
        return total

    def _account_balances(self) -> dict[str, dict[str, int]]:
        balances: dict[str, dict[str, int]] = defaultdict(
            lambda: {"actual": 0, "pending": 0, "cleared": 0}
        )
        for transaction in self.db.fetch_all(
            "SELECT account_id, amount_minor, status FROM current_transactions"
        ):
            balance = balances[transaction["account_id"]]
            balance["actual"] += transaction["amount_minor"]
            if transaction["status"] == STATUS_CLEARED:
                balance["cleared"] += transaction["amount_minor"]
            else:
                balance["pending"] += transaction["amount_minor"]
        return dict(balances)

    def _validate_transaction_payload(self, payload: dict[str, Any]) -> None:
        has_category = payload.get("category_id") is not None
        has_system = payload.get("system_category") is not None
        if has_category == has_system:
            raise ValueError("Exactly one of category_id or system_category must be set")

    def _create_credit_card_payment_category(
        self, connection: Any, account_name: str, now: datetime
    ) -> str:
        payment_name = f"{account_name} Payment"
        category_id = str(uuid4())
        insert_version(
            connection,
            "categories",
            {
                "category_id": category_id,
                "group_id": str(SYSTEM_CREDIT_CARD_GROUP_ID),
                "name": payment_name,
                "category_kind": CATEGORY_KIND_CREDIT_CARD_PAYMENT,
                "sort_order": 9999,
                "is_hidden": False,
                "is_active": True,
                "target_amount_minor": None,
                "due_date_rule": None,
                "metadata": json_dumps({"linked_account_name": account_name}),
                "valid_from": now,
                "valid_to": MAX_TS,
                "created_at": now,
                "created_by_user_id": None,
            },
        )
        insert_version(
            connection,
            "budget_buckets",
            {
                "bucket_id": self._bucket_id_for_category(category_id),
                "bucket_type": BUCKET_TYPE_CATEGORY,
                "category_id": category_id,
                "is_allocatable": True,
                "is_deletable": False,
                "valid_from": now,
                "valid_to": MAX_TS,
                "created_at": now,
                "created_by_user_id": None,
            },
        )
        return category_id

    def _bucket_id_from_name(self, name: str, categories: dict[str, Any]) -> str:
        if name.casefold() == "available to budget":
            return str(SYSTEM_ATB_BUCKET_ID)
        return self._bucket_id_for_category(categories[name].category_id)

    def _bucket_id_for_category(self, category_id: str) -> str:
        return str(uuid5(NAMESPACE_URL, f"dojo:bucket:{category_id}"))

    def _tracking_account_id(self, raw_name: str) -> str:
        return str(uuid5(NAMESPACE_URL, f"dojo:tracking:{raw_name}"))

    def _month_bounds(self, month: str) -> tuple[date, date]:
        year, month_number = month.split("-", maxsplit=1)
        month_start = date(int(year), int(month_number), 1)
        if month_start.month == 12:
            month_end = date(month_start.year + 1, 1, 1).fromordinal(
                date(month_start.year + 1, 1, 1).toordinal() - 1
            )
        else:
            next_month = date(month_start.year, month_start.month + 1, 1)
            month_end = date.fromordinal(next_month.toordinal() - 1)
        return month_start, month_end

    def _decode_json_fields(self, row: dict[str, Any], fields: set[str]) -> dict[str, Any]:
        decoded = dict(row)
        for field in fields:
            if decoded.get(field) is not None and isinstance(decoded[field], str):
                decoded[field] = __import__("json").loads(decoded[field])
        return decoded
