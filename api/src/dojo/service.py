from __future__ import annotations

from collections import defaultdict
from dataclasses import replace
from datetime import date, datetime, timedelta
from hashlib import sha256
from time import perf_counter
from typing import Any, cast
from uuid import NAMESPACE_URL, uuid4, uuid5

import duckdb

from dojo.account_values import (
    AccountValue,
    asset_value,
    ledger_value,
    liability_value,
    unavailable_value,
)
from dojo.aggregate_validation import build_validation_report
from dojo.clock import Clock, SystemClock, budget_month
from dojo.commands import execute_financial_command
from dojo.constants import (
    ACCOUNT_CLASS_BUDGET,
    ACCOUNT_CLASS_INVESTMENT,
    ACCOUNT_CLASS_LOAN,
    ACCOUNT_CLASS_TANGIBLE_ASSET,
    ACCOUNT_CLASS_TRACKING,
    BUCKET_TYPE_ATB,
    BUCKET_TYPE_CATEGORY,
    BUDGET_ACCOUNT_TYPE_CREDIT_CARD,
    BUDGET_ACCOUNT_TYPE_DEPOSIT,
    CATEGORY_KIND_CREDIT_CARD_PAYMENT,
    CATEGORY_KIND_STANDARD,
    DERIVATION_METHOD_CC_SPEND_AND_TRANSFER,
    DERIVATION_METHOD_TRANSFER_IN_ONLY,
    LINK_BEHAVIOR_CREDIT_CARD_PAYMENT,
    LINK_BEHAVIOR_INVESTMENT_CONTRIBUTION,
    LINK_BEHAVIOR_LOAN_PAYMENT,
    MAX_TS,
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
from dojo.investment import position_amount_minor, position_metrics
from dojo.loan_projection import LoanProjectionTerms, PaymentFrequency, project_loan
from dojo.operations import create_transaction_operation, link_transaction_operation
from dojo.reconciliation import (
    LocalRecord,
    SourceRecord,
    baseline_digest,
    compare_records,
    source_digest,
    transaction_digest,
)
from dojo.scd import (
    batch_insert_versions,
    close_current_version,
    close_current_version_if_expected,
    insert_version,
    replace_current_version,
)
from dojo.sql import load_sql, render_sql
from dojo.transfer_boundary import TransferBoundaryFact, compute_transfer_boundary_adjustment


class ImportValidationError(Exception):
    def __init__(self, report: dict[str, Any]) -> None:
        super().__init__("Import validation failed")
        self.report = report


class TransactionNotFoundError(ValueError):
    pass


class TransactionVersionConflictError(ValueError):
    pass


_TREND_DAYS = {"7d": 7, "1m": 31, "3m": 93, "6m": 186, "1y": 366, "all": 36500}
_TREND_BUCKET = {"7d": "day", "1m": "day", "3m": "day", "6m": "week", "1y": "week", "all": "month"}


class DojoService:
    def __init__(
        self,
        duckdb_path: str | None = None,
        *,
        clock: Clock | None = None,
        database: Database | None = None,
    ) -> None:
        if database is None:
            if duckdb_path is None:
                raise ValueError("duckdb_path is required when no Database is provided")
            self.db = Database(duckdb_path)
        else:
            self.db = database
        self.clock = clock or SystemClock()
        self._assert_schema_ready()
        self._ensure_system_rows()

    def close(self) -> None:
        self.db.close()

    def _assert_schema_ready(self) -> None:
        try:
            row = self.db.fetch_one(load_sql("queries/schema_has_import_runs"))
        except duckdb.Error as exc:
            raise RuntimeError(
                "Failed to inspect the DuckDB schema before service startup"
            ) from exc
        if row is None:
            raise RuntimeError(
                "DuckDB schema is not provisioned. Run `python -m dojo.migrations <path>` or the canonical just command before starting the API or tests."
            )

    def _ensure_system_rows(self) -> None:
        now = self.clock.now()
        with self.db.transaction() as connection:
            group_count_row = connection.execute(
                load_sql("queries/count_current_category_group_by_id"),
                (str(SYSTEM_CREDIT_CARD_GROUP_ID),),
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
                load_sql("queries/count_current_budget_bucket_by_id"),
                (str(SYSTEM_ATB_BUCKET_ID),),
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
        latest_batch = self.db.fetch_one(load_sql("queries/latest_import_batch"))
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
        row = self.db.fetch_one(load_sql("queries/latest_import_run"))
        if row is None:
            return None
        decoded = self._decode_json_fields(row, {"summary", "validation_report"})
        decoded.pop("validation_report", None)
        return decoded

    def get_bootstrap(self) -> dict[str, Any]:
        return {
            "app_status": self.get_app_status(),
            "import_status": self.get_import_status(),
            "default_budget_month": self.default_budget_month(),
        }

    def default_budget_month(self) -> str:
        return budget_month(self.clock)

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
        started_at = self.clock.now()
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
                completed_at=self.clock.now(),
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
                completed_at=self.clock.now(),
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
            completed_at=self.clock.now(),
            status="succeeded",
            source_kind=source_kind,
            validation_passed=True,
            summary=validation_report["summary"],
            validation_report=validation_report,
            error_message=None,
        )
        return {
            "ok": True,
            "import_batch": self.db.fetch_one(load_sql("queries/latest_import_batch")),
            "validation_report": validation_report,
            "app_status": self.get_app_status(),
        }

    def _apply_import_bundle(self, bundle: ParsedImportBundle) -> dict[str, Any]:
        imported_at = self.clock.now()
        with self.db.transaction() as connection:
            self._clear_domain_tables(connection)
            self._insert_bundle(connection, bundle, imported_at)
            report = self._validate_bundle(bundle)
            if report["hard_failures"]:
                raise ImportValidationError(report)
            connection.execute(
                load_sql("queries/insert_import_batch"),
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
            "investment_positions",
            "investment_cash_snapshots",
            "investment_price_snapshots",
            "account_budget_links",
            "tangible_asset_valuations",
            "loan_balance_snapshots",
            "loan_details",
            "investment_account_details",
            "tracking_account_details",
            "budget_account_settings",
            "accounts",
            "import_batches",
        ):
            connection.execute(render_sql("templates/delete_from_table", table=table))

    def _insert_bundle(
        self,
        connection: Any,
        bundle: ParsedImportBundle,
        imported_at: datetime,
        phase_timings: dict[str, float] | None = None,
    ) -> None:
        def run_phase(name: str, fn: Any) -> Any:
            start = perf_counter()
            result = fn()
            if phase_timings is not None:
                phase_timings[name] = (perf_counter() - start) * 1000
            return result

        group_by_name = {group.name: group for group in bundle.groups}
        category_by_name = {category.name: category for category in bundle.categories}
        account_ids_by_name = {account.name: account.account_id for account in bundle.accounts}

        group_rows: list[dict[str, Any]] = []

        def prepare_groups() -> None:
            for group in bundle.groups:
                group_id = (
                    str(SYSTEM_CREDIT_CARD_GROUP_ID)
                    if group.is_system and group.name == "Credit Card Payments"
                    else group.group_id
                )
                group_rows.append(
                    {
                        "row_id": str(uuid4()),
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
                    }
                )

        run_phase("prepare_groups_ms", prepare_groups)
        run_phase(
            "write_groups_ms",
            lambda: batch_insert_versions(connection, "category_groups", group_rows),
        )

        account_rows: list[dict[str, Any]] = []

        def prepare_accounts() -> None:
            for account in bundle.accounts:
                account_rows.append(
                    {
                        "row_id": str(uuid4()),
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
                    }
                )

        run_phase("prepare_accounts_ms", prepare_accounts)
        run_phase(
            "write_accounts_ms",
            lambda: batch_insert_versions(connection, "accounts", account_rows),
        )

        category_rows: list[dict[str, Any]] = []
        bucket_rows: list[dict[str, Any]] = [
            {
                "row_id": str(uuid4()),
                "bucket_id": str(SYSTEM_ATB_BUCKET_ID),
                "bucket_type": BUCKET_TYPE_ATB,
                "category_id": None,
                "is_allocatable": True,
                "is_deletable": False,
                "valid_from": imported_at,
                "valid_to": MAX_TS,
                "created_at": imported_at,
                "created_by_user_id": None,
            }
        ]

        def prepare_categories_and_buckets() -> None:
            for category in bundle.categories:
                group = group_by_name[category.group_name]
                group_id = (
                    str(SYSTEM_CREDIT_CARD_GROUP_ID)
                    if group.is_system and group.name == "Credit Card Payments"
                    else group.group_id
                )
                category_rows.append(
                    {
                        "row_id": str(uuid4()),
                        "category_id": category.category_id,
                        "group_id": group_id,
                        "name": category.name,
                        "category_kind": category.category_kind,
                        "sort_order": category.sort_order,
                        "is_hidden": category.is_hidden,
                        "is_active": category.is_active,
                        "target_amount_minor": None,
                        "due_date_rule": category.due_date_rule,
                        "metadata": json_dumps(
                            {"linked_account_name": category.linked_account_name}
                        ),
                        "valid_from": imported_at,
                        "valid_to": MAX_TS,
                        "created_at": imported_at,
                        "created_by_user_id": None,
                    }
                )
                bucket_rows.append(
                    {
                        "row_id": str(uuid4()),
                        "bucket_id": self._bucket_id_for_category(category.category_id),
                        "bucket_type": BUCKET_TYPE_CATEGORY,
                        "category_id": category.category_id,
                        "is_allocatable": True,
                        "is_deletable": category.category_kind != CATEGORY_KIND_CREDIT_CARD_PAYMENT,
                        "valid_from": imported_at,
                        "valid_to": MAX_TS,
                        "created_at": imported_at,
                        "created_by_user_id": None,
                    }
                )

        run_phase("prepare_categories_and_buckets_ms", prepare_categories_and_buckets)
        run_phase(
            "write_categories_ms",
            lambda: batch_insert_versions(connection, "categories", category_rows),
        )
        run_phase(
            "write_budget_buckets_ms",
            lambda: batch_insert_versions(connection, "budget_buckets", bucket_rows),
        )

        budget_setting_rows: list[dict[str, Any]] = []

        def prepare_budget_settings() -> None:
            for account in bundle.accounts:
                if (
                    account.account_class != ACCOUNT_CLASS_BUDGET
                    or account.budget_account_type is None
                ):
                    continue
                budget_setting_rows.append(
                    {
                        "row_id": str(uuid4()),
                        "account_id": account.account_id,
                        "budget_account_type": account.budget_account_type,
                        "display_liability_positive": account.display_liability_positive,
                        "valid_from": imported_at,
                        "valid_to": MAX_TS,
                        "created_at": imported_at,
                        "created_by_user_id": None,
                    }
                )

        run_phase("prepare_budget_account_settings_ms", prepare_budget_settings)
        run_phase(
            "write_budget_account_settings_ms",
            lambda: batch_insert_versions(
                connection,
                "budget_account_settings",
                budget_setting_rows,
            ),
        )

        cc_link_rows: list[dict[str, Any]] = []

        def prepare_account_budget_links() -> None:
            for account in bundle.accounts:
                if (
                    account.account_class != ACCOUNT_CLASS_BUDGET
                    or account.budget_account_type != BUDGET_ACCOUNT_TYPE_CREDIT_CARD
                    or not account.linked_payment_category_name
                ):
                    continue
                category_id = category_by_name[account.linked_payment_category_name].category_id
                cc_link_rows.append(
                    {
                        "row_id": str(uuid4()),
                        "account_id": account.account_id,
                        "category_id": category_id,
                        "link_behavior": LINK_BEHAVIOR_CREDIT_CARD_PAYMENT,
                        "derivation_method": DERIVATION_METHOD_CC_SPEND_AND_TRANSFER,
                        "effective_date": imported_at.date(),
                        "valid_from": imported_at,
                        "valid_to": MAX_TS,
                        "created_at": imported_at,
                        "created_by_user_id": None,
                    }
                )

        run_phase("prepare_account_budget_links_ms", prepare_account_budget_links)
        run_phase(
            "write_account_budget_links_ms",
            lambda: batch_insert_versions(
                connection,
                "account_budget_links",
                cc_link_rows,
            ),
        )

        tx_rows: list[dict[str, Any]] = []

        def prepare_transactions() -> None:
            for transaction in bundle.transactions:
                transaction_account_id = account_ids_by_name[transaction.account_name]
                category_id = (
                    category_by_name[transaction.category_name].category_id
                    if transaction.category_name
                    else None
                )
                tx_rows.append(
                    {
                        "row_id": str(uuid4()),
                        "transaction_id": transaction.transaction_id,
                        "date": transaction.date,
                        "account_id": transaction_account_id,
                        "amount_minor": transaction.amount_minor,
                        "category_id": category_id,
                        "system_category": transaction.system_category,
                        "status": transaction.status,
                        "memo": transaction.memo,
                        "entry_order": transaction.source_row_offset,
                        "valid_from": imported_at,
                        "valid_to": MAX_TS,
                        "created_at": imported_at,
                        "created_by_user_id": None,
                    }
                )

        run_phase("prepare_transactions_ms", prepare_transactions)
        run_phase(
            "write_transactions_ms",
            lambda: batch_insert_versions(
                connection,
                "transactions",
                tx_rows,
                batch_size=2_000,
            ),
        )

        alloc_rows: list[dict[str, Any]] = []

        def prepare_allocations() -> None:
            for allocation in bundle.allocations:
                alloc_rows.append(
                    {
                        "row_id": str(uuid4()),
                        "allocation_id": allocation.allocation_id,
                        "date": allocation.date,
                        "from_bucket_id": self._bucket_id_from_name(
                            allocation.from_name, category_by_name
                        ),
                        "to_bucket_id": self._bucket_id_from_name(
                            allocation.to_name, category_by_name
                        ),
                        "amount_minor": allocation.amount_minor,
                        "memo": allocation.memo,
                        "valid_from": imported_at,
                        "valid_to": MAX_TS,
                        "created_at": imported_at,
                        "created_by_user_id": None,
                    }
                )

        run_phase("prepare_allocations_ms", prepare_allocations)
        run_phase(
            "write_allocations_ms",
            lambda: batch_insert_versions(connection, "allocations", alloc_rows),
        )

        tracking_account_rows: list[dict[str, Any]] = []
        tracking_detail_rows: list[dict[str, Any]] = []
        valuation_rows: list[dict[str, Any]] = []
        tracking_account_ids_by_name: dict[str, str] = {}

        def prepare_valuations() -> None:
            for valuation in bundle.valuations:
                account_id: str | None = None
                if valuation.account_name is not None:
                    account_id = account_ids_by_name[valuation.account_name]
                elif valuation.raw_name not in tracking_account_ids_by_name:
                    new_account_id = self._tracking_account_id(valuation.raw_name)
                    tracking_account_ids_by_name[valuation.raw_name] = new_account_id
                    tracking_account_rows.append(
                        {
                            "row_id": str(uuid4()),
                            "account_id": new_account_id,
                            "account_class": ACCOUNT_CLASS_TRACKING,
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
                        }
                    )
                    tracking_detail_rows.append(
                        {
                            "row_id": str(uuid4()),
                            "account_id": new_account_id,
                            "polarity": "LIABILITY" if valuation.is_debt else "ASSET",
                            "source": "import",
                            "apy_minor": None,
                            "valid_from": imported_at,
                            "valid_to": MAX_TS,
                            "created_at": imported_at,
                            "created_by_user_id": None,
                        }
                    )
                    account_id = new_account_id
                else:
                    account_id = tracking_account_ids_by_name[valuation.raw_name]

                valuation_rows.append(
                    {
                        "row_id": str(uuid4()),
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
                    }
                )

        run_phase("prepare_valuations_ms", prepare_valuations)
        run_phase(
            "write_tracking_accounts_ms",
            lambda: batch_insert_versions(
                connection,
                "accounts",
                tracking_account_rows,
            ),
        )
        run_phase(
            "write_tracking_account_details_ms",
            lambda: batch_insert_versions(
                connection,
                "tracking_account_details",
                tracking_detail_rows,
            ),
        )
        run_phase(
            "write_valuations_ms",
            lambda: batch_insert_versions(
                connection,
                "net_worth_valuations",
                valuation_rows,
            ),
        )

    @staticmethod
    def _normalized_similarity(a: str, b: str) -> float:
        """Simple normalized Levenshtein-style similarity for fuzzy matching."""
        a = a.lower().strip()
        b = b.lower().strip()
        if a == b:
            return 1.0
        len_a, len_b = len(a), len(b)
        if len_a == 0 or len_b == 0:
            return 0.0
        matrix = list(range(len_b + 1))
        for i in range(1, len_a + 1):
            prev = matrix[0]
            matrix[0] = i
            for j in range(1, len_b + 1):
                cost = 0 if a[i - 1] == b[j - 1] else 1
                prev, matrix[j] = matrix[j], min(matrix[j] + 1, matrix[j - 1] + 1, prev + cost)
        max_len = max(len_a, len_b)
        return 1.0 - (matrix[len_b] / max_len)

    @staticmethod
    def _confidence_for_score(score: float) -> str:
        if score >= 0.92:
            return "HIGH"
        if score >= 0.82:
            return "MEDIUM"
        if score >= 0.70:
            return "LOW"
        return "NONE"

    def analyze_import_draft(
        self,
        *,
        source: str,
        source_kind: str,
        spreadsheet_title: str | None = None,
        named_ranges: dict[str, list[list[str]]] | None = None,
        available_named_ranges: list[str] | None = None,
        expected: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        if source_kind == "fixture":
            bundle = fixture_bundle()
        else:
            if named_ranges is None or spreadsheet_title is None:
                raise ValueError("Live import requires named range data")
            bundle = parse_named_range_workbook(
                spreadsheet_id=extract_sheet_id(source),
                spreadsheet_title=spreadsheet_title,
                named_ranges=named_ranges,
                source_kind=source_kind,
                expected=expected,
                available_named_ranges=available_named_ranges,
            )

        account_names_by_id: dict[str, str] = {}
        account_ids_by_name: dict[str, str] = {}
        for account in bundle.accounts:
            account_names_by_id[account.account_id] = account.name
            account_ids_by_name[account.name] = account.account_id

        latest_by_raw: dict[str, tuple[date, int]] = {}
        for valuation in bundle.valuations:
            existing = latest_by_raw.get(valuation.raw_name)
            if existing is None or valuation.effective_date >= existing[0]:
                latest_by_raw[valuation.raw_name] = (
                    valuation.effective_date,
                    valuation.amount_minor,
                )

        review_items: list[dict[str, Any]] = []
        seen_raws: set[str] = set()
        for valuation in bundle.valuations:
            if valuation.raw_name in seen_raws:
                continue
            seen_raws.add(valuation.raw_name)

            best_account_id: str | None = None
            best_account_name: str | None = None
            best_score = 0.0
            for name, account_id in account_ids_by_name.items():
                score = self._normalized_similarity(valuation.raw_name, name)
                if score > best_score:
                    best_score = score
                    best_account_id = account_id
                    best_account_name = name

            confidence = self._confidence_for_score(best_score)
            polarity = "LIABILITY" if valuation.is_debt else "ASSET"
            polarity_reason = (
                "Polarity set from Aspire debt config"
                if valuation.is_debt
                else "Polarity set from Aspire asset config"
            )

            if best_account_id and confidence in ("HIGH", "MEDIUM"):
                suggested_treatment = "DUPLICATE_BUDGET_ACCOUNT"
                reason = f"Matched budget account {best_account_name}"
            elif confidence == "LOW":
                suggested_treatment = "IMPORT_TRACKING_ACCOUNT"
                reason = f"Fuzzy match {best_score:.0%} confidence; review recommended"
            else:
                suggested_treatment = "IMPORT_TRACKING_ACCOUNT"
                reason = "No budget account match found"
                best_account_id = None

            latest_date, latest_amount = latest_by_raw.get(valuation.raw_name, (date.min, 0))

            review_items.append(
                {
                    "raw_name": valuation.raw_name,
                    "latest_value_minor": latest_amount,
                    "latest_date": str(latest_date),
                    "suggested_treatment": suggested_treatment,
                    "suggested_matched_account_id": best_account_id,
                    "suggested_matched_account_name": best_account_name,
                    "suggested_polarity": polarity,
                    "suggested_polarity_reason": polarity_reason,
                    "confidence": confidence,
                    "score": best_score,
                    "reason": reason,
                    "candidate_account_ids": [
                        account_ids_by_name[name] for name in sorted(account_ids_by_name.keys())
                    ],
                    "candidate_account_names": sorted(account_ids_by_name.keys()),
                }
            )

        draft_id = str(uuid4())
        now = self.clock.now()
        draft_payload = {
            "source": source,
            "source_kind": source_kind,
            "spreadsheet_title": spreadsheet_title,
            "named_ranges": named_ranges,
            "available_named_ranges": available_named_ranges,
            "expected": expected,
        }

        with self.db.transaction() as connection:
            connection.execute(
                load_sql("queries/insert_import_draft"),
                (
                    draft_id,
                    now,
                    source_kind,
                    extract_sheet_id(source),
                    spreadsheet_title,
                    json_dumps(draft_payload),
                    json_dumps(
                        {
                            "budget_account_count": len(
                                [
                                    a
                                    for a in bundle.accounts
                                    if a.account_class == ACCOUNT_CLASS_BUDGET
                                ]
                            ),
                            "net_worth_category_count": len(
                                {v.raw_name for v in bundle.valuations}
                            ),
                            "review_items": review_items,
                        }
                    ),
                ),
            )

        return {
            "draft_id": draft_id,
            "budget_account_count": len(
                [a for a in bundle.accounts if a.account_class == ACCOUNT_CLASS_BUDGET]
            ),
            "net_worth_category_count": len({v.raw_name for v in bundle.valuations}),
            "review_items": review_items,
        }

    def commit_import_draft(
        self,
        *,
        draft_id: str,
        decisions: list[dict[str, Any]],
        low_confidence_confirmed: bool,
    ) -> dict[str, Any]:
        draft = self.db.fetch_one(load_sql("queries/import_draft_by_id"), (draft_id,))
        if draft is None or draft["status"] != "pending":
            raise ValueError("Draft not found or already used")

        import json as json_mod

        draft_payload = json_mod.loads(draft["payload"])
        preview = json_mod.loads(draft["preview"])
        review_items = preview["review_items"]

        item_by_name = {item["raw_name"]: item for item in review_items}
        decision_by_name = self._parse_import_decisions(review_items, decisions)

        low_count = 0
        for item in review_items:
            decision = decision_by_name[item["raw_name"]]
            is_unchanged = (
                decision.get("treatment", item["suggested_treatment"])
                == item["suggested_treatment"]
                and decision.get("matched_account_id", item["suggested_matched_account_id"])
                == item["suggested_matched_account_id"]
                and decision.get("polarity", item["suggested_polarity"])
                == item["suggested_polarity"]
            )
            if is_unchanged and item["confidence"] == "LOW":
                low_count += 1

        if low_count > 0 and not low_confidence_confirmed:
            return {
                "ok": False,
                "error": "Low-confidence decisions require confirmation",
                "low_confidence_count": low_count,
            }

        source = draft_payload["source"]
        source_kind = draft_payload["source_kind"]
        spreadsheet_title = draft_payload.get("spreadsheet_title")
        named_ranges = draft_payload.get("named_ranges")
        available_named_ranges = draft_payload.get("available_named_ranges")
        expected = draft_payload.get("expected")

        if source_kind == "fixture":
            bundle = fixture_bundle()
        else:
            if named_ranges is None or spreadsheet_title is None:
                raise ValueError("Draft missing required named range data")
            bundle = parse_named_range_workbook(
                spreadsheet_id=extract_sheet_id(source),
                spreadsheet_title=spreadsheet_title,
                named_ranges=named_ranges,
                source_kind=source_kind,
                expected=expected,
                available_named_ranges=available_named_ranges,
            )

        account_ids_by_name: dict[str, str] = {
            account.name: account.account_id for account in bundle.accounts
        }
        account_names_by_id = {account_id: name for name, account_id in account_ids_by_name.items()}

        decisions_summary = {
            "duplicates_excluded": 0,
            "tracking_created": 0,
            "skipped": 0,
            "low_confidence_accepted": low_count,
        }
        duplicate_categories: set[str] = set()
        tracking_categories: set[str] = set()
        skipped_categories: set[str] = set()
        committed_valuations = []

        for valuation in bundle.valuations:
            decision = decision_by_name[valuation.raw_name]
            treatment = decision["treatment"]

            if treatment == "DO_NOT_IMPORT":
                skipped_categories.add(valuation.raw_name)
                continue

            if treatment == "DUPLICATE_BUDGET_ACCOUNT":
                matched_account_id = decision.get("matched_account_id")
                matched_account_name = (
                    account_names_by_id.get(matched_account_id)
                    if isinstance(matched_account_id, str)
                    else None
                )
                if matched_account_name:
                    valuation.account_name = matched_account_name
                    duplicate_categories.add(valuation.raw_name)
                    committed_valuations.append(valuation)
                    continue

            if treatment == "IMPORT_TRACKING_ACCOUNT":
                original_raw_name = valuation.raw_name
                suggested_polarity = item_by_name.get(valuation.raw_name, {}).get(
                    "suggested_polarity", "ASSET"
                )
                polarity = decision.get("polarity", suggested_polarity)
                tracking_categories.add(original_raw_name)

                valuation.account_name = None
                if original_raw_name in account_ids_by_name:
                    valuation.raw_name = f"{original_raw_name} (tracking)"
                valuation.is_debt = polarity == "LIABILITY"
                committed_valuations.append(valuation)

        bundle.valuations = committed_valuations
        decisions_summary["duplicates_excluded"] = len(duplicate_categories)
        decisions_summary["tracking_created"] = len(tracking_categories)
        decisions_summary["skipped"] = len(skipped_categories)
        import_summary = {
            "account_count": len(bundle.accounts) + len(tracking_categories),
            "category_count": len(bundle.categories),
            "group_count": len(bundle.groups),
            "transaction_count": len(bundle.transactions),
            "allocation_count": len(bundle.allocations),
            "valuation_count": len(bundle.valuations),
        }

        imported_at = self.clock.now()
        import_run_id = str(uuid4())
        try:
            with self.db.transaction() as connection:
                claimed = connection.execute(
                    load_sql("queries/claim_import_draft"), (draft_id,)
                ).fetchone()
                if claimed is None:
                    raise ValueError("Draft not found or already used")
                self._clear_domain_tables(connection)
                self._insert_bundle(connection, bundle, imported_at)
                validation_report = self._validate_bundle(bundle)
                if validation_report["hard_failures"]:
                    raise ImportValidationError(validation_report)
                connection.execute(
                    load_sql("queries/insert_import_batch"),
                    (
                        str(uuid4()),
                        bundle.spreadsheet_id,
                        bundle.spreadsheet_title,
                        imported_at,
                        imported_at,
                        json_dumps(
                            validation_report["summary"] | {"decisions_summary": decisions_summary}
                        ),
                    ),
                )
        except ImportValidationError as exc:
            self._record_import_run(
                import_run_id=import_run_id,
                spreadsheet_id=bundle.spreadsheet_id,
                spreadsheet_title=bundle.spreadsheet_title,
                started_at=imported_at,
                completed_at=self.clock.now(),
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

        self._record_import_run(
            import_run_id=import_run_id,
            spreadsheet_id=bundle.spreadsheet_id,
            spreadsheet_title=bundle.spreadsheet_title,
            started_at=imported_at,
            completed_at=self.clock.now(),
            status="succeeded",
            source_kind=source_kind,
            validation_passed=True,
            summary=validation_report["summary"],
            validation_report=validation_report,
            error_message=None,
        )

        return {
            "ok": True,
            "import_summary": import_summary,
            "decisions_summary": decisions_summary,
            "validation_report": validation_report,
            "import_batch": self.db.fetch_one(load_sql("queries/latest_import_batch")),
            "app_status": self.get_app_status(),
            "import_status": self.get_import_status(),
        }

    @staticmethod
    def _parse_import_decisions(
        review_items: list[dict[str, Any]], decisions: list[dict[str, Any]]
    ) -> dict[str, dict[str, Any]]:
        expected_names = {str(item["raw_name"]) for item in review_items}
        decision_names = [str(decision["raw_name"]) for decision in decisions]
        if len(decision_names) != len(set(decision_names)):
            raise ValueError("Import review contains duplicate decisions")
        provided_names = set(decision_names)
        if provided_names != expected_names:
            missing = sorted(expected_names - provided_names)
            unknown = sorted(provided_names - expected_names)
            details = []
            if missing:
                details.append(f"missing: {', '.join(missing)}")
            if unknown:
                details.append(f"unknown: {', '.join(unknown)}")
            raise ValueError(f"Import review decisions do not match preview ({'; '.join(details)})")

        items_by_name = {str(item["raw_name"]): item for item in review_items}
        parsed = {str(decision["raw_name"]): decision for decision in decisions}
        for raw_name, decision in parsed.items():
            treatment = decision["treatment"]
            if treatment == "DUPLICATE_BUDGET_ACCOUNT":
                matched_account_id = decision.get("matched_account_id")
                candidates = set(items_by_name[raw_name].get("candidate_account_ids", []))
                if not matched_account_id or matched_account_id not in candidates:
                    raise ValueError(
                        f"Duplicate decision for {raw_name} needs a valid account match"
                    )
            if treatment == "IMPORT_TRACKING_ACCOUNT" and decision.get("polarity") not in {
                "ASSET",
                "LIABILITY",
            }:
                raise ValueError(f"Tracking decision for {raw_name} needs a polarity")
        return parsed

    def _validate_bundle(self, bundle: ParsedImportBundle) -> dict[str, Any]:
        return build_validation_report(self, bundle)

    def snapshot_for_validation(self, months: list[str]) -> dict[str, Any]:
        default_month = self.default_budget_month()
        accounts = self.list_accounts(show_hidden=True)
        categories_by_month: dict[str, list[dict[str, Any]]] = {
            default_month: self.list_categories(month=default_month, show_hidden=True)
        }
        account_balances = {
            account["name"]: {
                "actual": account["actual_balance_minor"],
                "pending": account["pending_balance_minor"],
                "cleared": account["cleared_balance_minor"],
            }
            for account in accounts
            if account["account_class"] == ACCOUNT_CLASS_BUDGET
        }
        default_categories = categories_by_month[default_month]
        category_available = {
            category["name"]: category["available_minor"] for category in default_categories
        }
        month_activity: dict[str, dict[str, int]] = {}
        month_budgeted: dict[str, dict[str, int]] = {}
        starting_available: dict[str, dict[str, int]] = {}
        for month in months:
            categories = categories_by_month.get(month)
            if categories is None:
                categories = self.list_categories(month=month, show_hidden=True)
                categories_by_month[month] = categories
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
            "account_count": len(accounts),
            "category_group_count": len(
                self.list_category_groups(
                    month=default_month,
                    show_hidden=True,
                    precomputed_categories=default_categories,
                )
            ),
            "category_count": len(default_categories),
            "net_worth_valuation_rows": len(
                self.db.fetch_all(load_sql("queries/current_net_worth_valuations"))
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
            load_sql("queries/insert_import_run"),
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
        accounts = self.db.fetch_all(load_sql("queries/list_accounts"))
        today = self.clock.today()
        balances = self._account_balances(today)
        previous_balances = self._account_balances(today - timedelta(days=30))
        values = self._account_values(accounts, balances, previous_balances, today)
        cutover_relations = self.db.fetch_all(load_sql("queries/tracking_cutover_relations"))
        retired_predecessors = {
            str(row["predecessor_account_id"])
            for row in cutover_relations
            if row["cutover_date"] <= today
        }
        pending_successors = {
            str(row["successor_account_id"])
            for row in cutover_relations
            if row["cutover_date"] > today
        }
        results = []
        for account in accounts:
            account_id = str(account["account_id"])
            effective_active = bool(account["is_active"]) and account_id not in (
                retired_predecessors | pending_successors
            )
            if (account["is_hidden"] or not effective_active) and not show_hidden:
                continue
            account_balances = balances.get(account_id, {"actual": 0, "pending": 0, "cleared": 0})
            display_balance = account_balances["actual"]
            if account.get(
                "budget_account_type"
            ) == BUDGET_ACCOUNT_TYPE_CREDIT_CARD and account.get("display_liability_positive"):
                display_balance = -display_balance
            value = values[account_id]
            if account["account_class"] in {ACCOUNT_CLASS_BUDGET, ACCOUNT_CLASS_INVESTMENT}:
                reconciliation_status = self.get_reconciliation_status(account_id)
                if not (
                    account["account_class"] == ACCOUNT_CLASS_INVESTMENT
                    and reconciliation_status == "NOT_RECONCILED"
                ):
                    value = replace(value, reconciliation_status=reconciliation_status)
            results.append(
                account
                | {
                    "is_active": effective_active,
                    "actual_balance_minor": account_balances["actual"],
                    "pending_balance_minor": account_balances["pending"],
                    "cleared_balance_minor": account_balances["cleared"],
                    "display_balance_minor": display_balance,
                    "current_value_minor": value.current_value_minor,
                    "net_worth_contribution_minor": value.net_worth_minor,
                    "value_source": value.source_of_truth,
                    "value_effective_date": (
                        str(value.effective_date) if value.effective_date else None
                    ),
                    "change_30d_minor": value.change_minor,
                    "reconciliation_status": value.reconciliation_status,
                    "provisional_value_minor": value.provisional_minor,
                    "liability_component_minor": value.liability_minor,
                    "restricted_asset_component_minor": value.restricted_asset_minor,
                    "unapplied_credit_component_minor": value.unapplied_credit_minor,
                    # Compatibility aliases for the current frontend while detail
                    # pages migrate to the explicit value contract.
                    "latest_valuation_minor": value.current_value_minor,
                    "latest_valuation_date": (
                        str(value.effective_date) if value.effective_date else None
                    ),
                }
            )
        return results

    def get_assets_liabilities(self) -> dict[str, Any]:
        accounts = self.list_accounts(show_hidden=False)
        groups: dict[str, list[dict[str, Any]]] = {
            "CASH": [],
            "INVESTMENTS": [],
            "TANGIBLE_ASSETS": [],
            "RESTRICTED_ASSETS": [],
            "TRACKING_ASSETS": [],
            "CREDIT": [],
            "LOANS": [],
            "TRACKING_LIABILITIES": [],
        }
        group_totals: dict[str, int] = {
            "CASH": 0,
            "INVESTMENTS": 0,
            "TANGIBLE_ASSETS": 0,
            "RESTRICTED_ASSETS": 0,
            "TRACKING_ASSETS": 0,
            "CREDIT": 0,
            "LOANS": 0,
            "TRACKING_LIABILITIES": 0,
        }
        asset_total = 0
        liability_total = 0
        needs_attention = 0
        changes: list[int | None] = []

        for account in accounts:
            account_class = account["account_class"]
            budget_type = account.get("budget_account_type")
            display_balance = account["display_balance_minor"]
            value = account.get("current_value_minor")
            net_worth = int(account.get("net_worth_contribution_minor", 0))
            attention_status = (
                "AWAITING_STATEMENT"
                if value is None and account_class == ACCOUNT_CLASS_LOAN
                else "MISSING_VALUE"
                if value is None
                else account["reconciliation_status"]
            )
            if attention_status != "CURRENT":
                needs_attention += 1
            changes.append(account["change_30d_minor"])
            item = account | {
                "source_of_truth": account["value_source"],
                "value_minor": net_worth,
                "change_30d_minor": account["change_30d_minor"],
                "value_effective_date": account["value_effective_date"],
                "attention_status": attention_status,
            }

            if account_class == ACCOUNT_CLASS_BUDGET:
                if budget_type == BUDGET_ACCOUNT_TYPE_CREDIT_CARD:
                    amount = account["actual_balance_minor"]
                    groups["CREDIT"].append(item | {"value_minor": amount})
                    group_totals["CREDIT"] += amount
                    liability_total += min(amount, 0)
                else:
                    groups["CASH"].append(item | {"value_minor": display_balance})
                    group_totals["CASH"] += display_balance
                    asset_total += max(display_balance, 0)
            elif account_class == ACCOUNT_CLASS_INVESTMENT:
                amount = net_worth
                groups["INVESTMENTS"].append(item)
                group_totals["INVESTMENTS"] += amount
                asset_total += max(amount, 0)
            elif account_class == ACCOUNT_CLASS_TRACKING:
                amount = net_worth
                polarity = account.get("tracking_polarity", "ASSET")
                if polarity == "LIABILITY":
                    groups["TRACKING_LIABILITIES"].append(item)
                    group_totals["TRACKING_LIABILITIES"] += amount
                    liability_total += min(amount, 0)
                else:
                    groups["TRACKING_ASSETS"].append(item)
                    group_totals["TRACKING_ASSETS"] += amount
                    asset_total += max(amount, 0)
            elif account_class == ACCOUNT_CLASS_LOAN:
                liability = int(account.get("liability_component_minor", 0))
                escrow = int(account.get("restricted_asset_component_minor", 0))
                unapplied = int(account.get("unapplied_credit_component_minor", 0))
                groups["LOANS"].append(item | {"value_minor": liability})
                group_totals["LOANS"] += liability
                liability_total += liability
                if escrow:
                    groups["RESTRICTED_ASSETS"].append(
                        item
                        | {
                            "presentation_id": f"{account['account_id']}:escrow",
                            "name": f"{account['name']} escrow",
                            "value_minor": escrow,
                            "change_30d_minor": None,
                            "component_kind": "ESCROW",
                        }
                    )
                    group_totals["RESTRICTED_ASSETS"] += escrow
                    asset_total += escrow
                if unapplied:
                    groups["RESTRICTED_ASSETS"].append(
                        item
                        | {
                            "presentation_id": f"{account['account_id']}:unapplied-credit",
                            "name": f"{account['name']} unapplied credit",
                            "value_minor": unapplied,
                            "change_30d_minor": None,
                            "component_kind": "UNAPPLIED_CREDIT",
                        }
                    )
                    group_totals["RESTRICTED_ASSETS"] += unapplied
                    asset_total += unapplied
            elif account_class == ACCOUNT_CLASS_TANGIBLE_ASSET:
                amount = net_worth
                groups["TANGIBLE_ASSETS"].append(item)
                group_totals["TANGIBLE_ASSETS"] += amount
                asset_total += max(amount, 0)

        return {
            "assets_minor": asset_total,
            "liabilities_minor": liability_total,
            "net_worth_minor": asset_total + liability_total,
            "change_30d_minor": (
                sum(change for change in changes if change is not None)
                if changes and all(change is not None for change in changes)
                else None
            ),
            "needs_attention_count": needs_attention,
            "groups": [
                {
                    "key": key,
                    "items": items,
                    "total_minor": group_totals[key],
                }
                for key, items in groups.items()
                if items
            ],
        }

    def list_transactions(
        self,
        *,
        limit: int,
        offset: int = 0,
        show_hidden: bool,
        sort_by: str = "entry_order",
        sort_dir: str = "asc",
        account_id: str | None = None,
        category_id: str | None = None,
        status: str | None = None,
        date_from: str | None = None,
        date_to: str | None = None,
        amount_min_minor: int | None = None,
        amount_max_minor: int | None = None,
    ) -> dict[str, Any]:
        sort_expressions = {
            "date": {"asc": "date ASC", "desc": "date DESC"},
            "amount_minor": {"asc": "amount_minor ASC", "desc": "amount_minor DESC"},
            "status": {"asc": "status ASC", "desc": "status DESC"},
            "created_at": {"asc": "created_at ASC", "desc": "created_at DESC"},
            "entry_order": {"asc": "entry_order ASC", "desc": "entry_order DESC"},
        }
        sort_expression = sort_expressions.get(sort_by, sort_expressions["entry_order"])[
            "desc" if sort_dir == "desc" else "asc"
        ]

        accounts = {
            row["account_id"]: row
            for row in self.db.fetch_all(load_sql("queries/current_accounts"))
        }
        categories = {
            row["category_id"]: row
            for row in self.db.fetch_all(load_sql("queries/current_categories"))
        }

        hidden_account_ids: set[str] = set()
        hidden_category_ids: set[str] = set()
        if not show_hidden:
            hidden_account_ids = {aid for aid, a in accounts.items() if a["is_hidden"]}
            hidden_category_ids = {cid for cid, c in categories.items() if c["is_hidden"]}

        filter_clauses = ["1 = 1"]
        filter_params: list[Any] = []
        if hidden_account_ids:
            account_placeholders = ",".join("?" for _ in hidden_account_ids)
            filter_clauses.append(f"account_id NOT IN ({account_placeholders})")
            filter_params.extend(str(account_id) for account_id in hidden_account_ids)
        if hidden_category_ids:
            category_placeholders = ",".join("?" for _ in hidden_category_ids)
            filter_clauses.append(
                f"(category_id IS NULL OR category_id NOT IN ({category_placeholders}))"
            )
            filter_params.extend(str(category_id) for category_id in hidden_category_ids)
        if account_id:
            filter_clauses.append("account_id = ?")
            filter_params.append(account_id)
        if category_id:
            filter_clauses.append("category_id = ?")
            filter_params.append(category_id)
        if status:
            filter_clauses.append("status = ?")
            filter_params.append(status)
        if date_from:
            filter_clauses.append("date >= ?")
            filter_params.append(date_from)
        if date_to:
            filter_clauses.append("date <= ?")
            filter_params.append(date_to)
        if amount_min_minor is not None:
            filter_clauses.append("ABS(amount_minor) >= ?")
            filter_params.append(amount_min_minor)
        if amount_max_minor is not None:
            filter_clauses.append("ABS(amount_minor) <= ?")
            filter_params.append(amount_max_minor)

        filter_clause = " AND ".join(filter_clauses)
        total = self.db.fetch_one(
            render_sql(
                "queries/list_transactions_count_filtered",
                filter_clause=filter_clause,
            ),
            tuple(filter_params),
        )
        total_count = total["cnt"] if total else 0
        status_rows = self.db.fetch_all(
            render_sql(
                "queries/list_transactions_status_counts_filtered",
                filter_clause=filter_clause,
            ),
            tuple(filter_params),
        )
        status_counts = {"PENDING": 0, "CLEARED": 0}
        for status_row in status_rows:
            status_counts[str(status_row["status"])] = int(status_row["cnt"])

        query_params: list[Any] = list(filter_params)
        query_params.append(limit)
        query_params.append(offset)
        rows = self.db.fetch_all(
            render_sql(
                "queries/list_transactions_page_filtered",
                filter_clause=filter_clause,
                sort_expression=sort_expression,
            ),
            tuple(query_params),
        )

        operation_accounts: dict[str, list[dict[str, Any]]] = defaultdict(list)
        transaction_ids = [str(row["transaction_id"]) for row in rows]
        if transaction_ids:
            placeholders = ",".join("?" for _ in transaction_ids)
            for operation_row in self.db.fetch_all(
                render_sql(
                    "queries/transaction_operation_accounts_by_transaction_ids",
                    transaction_placeholders=placeholders,
                ),
                tuple(transaction_ids),
            ):
                operation_accounts[str(operation_row["transaction_id"])].append(operation_row)

        results: list[dict[str, Any]] = []
        for row in rows:
            account = accounts[row["account_id"]]
            category = categories.get(row["category_id"])
            hidden = account["is_hidden"] or (category["is_hidden"] if category else False)
            operation_counterpart = next(
                iter(operation_accounts.get(str(row["transaction_id"]), [])), None
            )
            counterpart = operation_counterpart
            results.append(
                {key: value for key, value in row.items() if key != "row_id"}
                | {
                    "version": str(row["row_id"]),
                    "account_name": account["name"],
                    "category_name": category["name"] if category else None,
                    "is_hidden_entity": hidden,
                    "transfer_counterparty_account_id": (
                        str(
                            counterpart.get("counterpart_account_id", counterpart.get("account_id"))
                        )
                        if counterpart
                        else None
                    ),
                    "transfer_counterparty_account_name": (
                        counterpart["account_name"] if counterpart else None
                    ),
                    "operation_id": (
                        str(operation_counterpart["operation_id"])
                        if operation_counterpart
                        else None
                    ),
                    "operation_kind": (
                        operation_counterpart["operation_kind"] if operation_counterpart else None
                    ),
                }
            )
        return {
            "items": results,
            "total": total_count,
            "offset": offset,
            "limit": limit,
            "has_more": (offset + limit) < total_count,
            "status_counts": status_counts,
        }

    def account_transaction_summary(
        self, *, account_id: str, days: int = 30, show_hidden: bool = False
    ) -> dict[str, Any]:
        today = self.clock.today()
        start_date = today - timedelta(days=days)
        account_class = self._account_class(account_id)
        if account_class in {ACCOUNT_CLASS_TRACKING, ACCOUNT_CLASS_TANGIBLE_ASSET}:
            query_name = (
                "queries/tracking_summary"
                if account_class == ACCOUNT_CLASS_TRACKING
                else "queries/tangible_summary"
            )
            row = self.db.fetch_one(
                load_sql(query_name),
                (start_date, today, account_id),
            )
            if row is None:
                anchor = self._account_display_balance(account_id)
                return {
                    "inflow_minor": 0,
                    "outflow_minor": 0,
                    "net_flow_minor": 0,
                    "transaction_count": 0,
                    "average_daily_balance_minor": anchor,
                }
            return {
                "inflow_minor": int(row["inflow_minor"]),
                "outflow_minor": int(row["outflow_minor"]),
                "net_flow_minor": int(row["net_flow_minor"]),
                "transaction_count": int(row["snapshot_count"]),
                "average_daily_balance_minor": int(row["average_daily_balance_minor"]),
            }
        anchor = self._account_display_balance(account_id)
        row = self.db.fetch_one(
            load_sql("queries/account_transaction_summary"),
            (start_date, today, account_id, anchor),
        )
        if row is None:
            return {
                "inflow_minor": 0,
                "outflow_minor": 0,
                "net_flow_minor": 0,
                "transaction_count": 0,
                "average_daily_balance_minor": anchor,
            }
        average = row["average_daily_balance_minor"]
        return {
            "inflow_minor": int(row["inflow_minor"]),
            "outflow_minor": int(row["outflow_minor"]),
            "net_flow_minor": int(row["net_flow_minor"]),
            "transaction_count": int(row["transaction_count"]),
            "average_daily_balance_minor": int(average) if average is not None else anchor,
        }

    def account_balance_trend(
        self, *, account_id: str, period: str, show_hidden: bool = False
    ) -> dict[str, Any]:
        bucket = _TREND_BUCKET[period]
        days = _TREND_DAYS[period]
        today = self.clock.today()
        date_from = today - timedelta(days=days)
        account_class = self._account_class(account_id)
        if account_class in {ACCOUNT_CLASS_TRACKING, ACCOUNT_CLASS_TANGIBLE_ASSET}:
            query_name = (
                "queries/tracking_balance_series"
                if account_class == ACCOUNT_CLASS_TRACKING
                else "queries/tangible_balance_series"
            )
            rows = self.db.fetch_all(
                load_sql(query_name),
                (account_id, date_from, today, account_id, date_from, date_from, today),
            )
            return {
                "points": [
                    {"date": str(row["date"]), "balance_minor": int(row["balance_minor"])}
                    for row in rows
                ]
            }
        anchor = self._account_display_balance(account_id)
        rows = self.db.fetch_all(
            render_sql("queries/account_balance_series", bucket=bucket),
            (anchor, account_id, date_from, today),
        )
        return {
            "points": [
                {"date": str(row["date"]), "balance_minor": int(row["balance_minor"])}
                for row in rows
            ]
        }

    def _account_display_balance(self, account_id: str) -> int:
        for account in self.list_accounts(show_hidden=True):
            if account["account_id"] == account_id:
                return int(account["display_balance_minor"])
        return 0

    def _account_class(self, account_id: str) -> str:
        for account in self.list_accounts(show_hidden=True):
            if account["account_id"] == account_id:
                return str(account.get("account_class", ""))
        return ""

    def list_allocations(self, *, show_hidden: bool) -> list[dict[str, Any]]:
        categories = self.list_categories(month=self.default_budget_month(), show_hidden=True)
        category_by_bucket_id = {category["bucket_id"]: category for category in categories}

        def bucket_label(bucket_id: Any) -> str:
            if str(bucket_id) == str(SYSTEM_ATB_BUCKET_ID):
                return "Available to budget"
            category = category_by_bucket_id.get(str(bucket_id))
            return category["name"] if category else "Unknown bucket"

        results: list[dict[str, Any]] = []
        for row in self.db.fetch_all(load_sql("queries/current_allocations")):
            from_category = category_by_bucket_id.get(str(row["from_bucket_id"]))
            to_category = category_by_bucket_id.get(str(row["to_bucket_id"]))
            if not show_hidden and (
                (from_category is not None and from_category["is_hidden"])
                or (to_category is not None and to_category["is_hidden"])
            ):
                continue
            results.append(
                row
                | {
                    "allocation_id": str(row["allocation_id"]),
                    "from_bucket_id": str(row["from_bucket_id"]),
                    "to_bucket_id": str(row["to_bucket_id"]),
                    "from_bucket_name": bucket_label(row["from_bucket_id"]),
                    "to_bucket_name": bucket_label(row["to_bucket_id"]),
                    "from_category_id": from_category["category_id"] if from_category else None,
                    "to_category_id": to_category["category_id"] if to_category else None,
                    "memo": row.get("memo")
                    or f"{bucket_label(row['from_bucket_id'])} to {bucket_label(row['to_bucket_id'])}",
                }
            )
        return sorted(results, key=lambda item: item["date"], reverse=True)

    def list_category_groups(
        self,
        *,
        month: str,
        show_hidden: bool,
        precomputed_categories: list[dict[str, Any]] | None = None,
    ) -> list[dict[str, Any]]:
        groups = self.db.fetch_all(load_sql("queries/current_category_groups_ordered"))
        categories = (
            precomputed_categories
            if precomputed_categories is not None
            else self.list_categories(month=month, show_hidden=True)
        )
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
        categories = self.db.fetch_all(load_sql("queries/current_categories_ordered"))
        groups = {
            row["group_id"]: row
            for row in self.db.fetch_all(load_sql("queries/current_category_groups"))
        }
        month_start, month_end = self._month_bounds(month)

        # Precompute account-budget link behavior (unified for all account types)
        current_account_links = self.db.fetch_all(
            load_sql("queries/current_account_budget_links_all")
        )
        transfer_link_intervals = self.db.fetch_all(
            load_sql("queries/account_budget_link_effective_intervals")
        )
        account_links = [
            link
            for link in current_account_links
            if link["derivation_method"] != DERIVATION_METHOD_TRANSFER_IN_ONLY
        ] + transfer_link_intervals
        link_behaviors: dict[str, list[dict[str, Any]]] = defaultdict(list)
        for link in account_links:
            link_behaviors[str(link["category_id"])].append(link)
        link_derived_by_cat: dict[str, int] = defaultdict(int)
        link_derived_month_by_cat: dict[str, int] = defaultdict(int)
        link_derived_pre_month_by_cat: dict[str, int] = defaultdict(int)
        for link in account_links:
            cat_id = str(link["category_id"])
            account_id = link["account_id"]
            derivation_method = link["derivation_method"]
            if derivation_method == DERIVATION_METHOD_TRANSFER_IN_ONLY:
                for t in self.db.fetch_all(
                    load_sql("queries/current_transfers_in_by_account_from_date"),
                    (account_id, link["effective_date"]),
                ):
                    if link.get("end_date") is not None and t["date"] >= link["end_date"]:
                        continue
                    link_derived_by_cat[cat_id] += t["amount_minor"]
                    if month_start <= t["date"] <= month_end:
                        link_derived_month_by_cat[cat_id] -= t["amount_minor"]
                    if t["date"] < month_start:
                        link_derived_pre_month_by_cat[cat_id] -= t["amount_minor"]
            elif derivation_method == DERIVATION_METHOD_CC_SPEND_AND_TRANSFER:
                # Credit card: sum categorized spending (as negative) plus transfer-in
                for t in self.db.fetch_all(
                    load_sql("queries/current_transactions_by_account_categorized"),
                    (account_id,),
                ):
                    link_derived_by_cat[cat_id] += -t["amount_minor"]
                for t in self.db.fetch_all(
                    load_sql("queries/current_transactions_by_account_positive_system_category"),
                    (account_id, SYSTEM_CATEGORY_TRANSFER),
                ):
                    link_derived_by_cat[cat_id] += -t["amount_minor"]

        # Precompute linked account ids for categories (used for context links)
        linked_account_id_by_cat: dict[str, str] = {
            row["category_id"]: row["account_id"] for row in current_account_links
        }

        # Precompute transaction sums per category (all-time for available, monthly for activity)
        tx_by_category: dict[str, int] = defaultdict(int)
        tx_month_activity: dict[str, int] = defaultdict(int)
        tx_pre_month: dict[str, int] = defaultdict(int)
        for t in self.db.fetch_all(load_sql("queries/current_transactions_category_amount_date")):
            cid = t["category_id"]
            amt = t["amount_minor"]
            tx_by_category[cid] += amt
            if month_start <= t["date"] <= month_end:
                tx_month_activity[cid] += amt
            if t["date"] < month_start:
                tx_pre_month[cid] += amt

        # Precompute allocation sums per bucket (all-time for available, monthly for budgeted, pre-month for carried over)
        alloc_to_bucket: dict[str, int] = defaultdict(int)
        alloc_from_bucket: dict[str, int] = defaultdict(int)
        alloc_month_to: dict[str, int] = defaultdict(int)
        alloc_month_from: dict[str, int] = defaultdict(int)
        alloc_pre_to: dict[str, int] = defaultdict(int)
        alloc_pre_from: dict[str, int] = defaultdict(int)
        for a in self.db.fetch_all(load_sql("queries/current_allocations_amount_date")):
            amt = a["amount_minor"]
            alloc_to_bucket[a["to_bucket_id"]] += amt
            alloc_from_bucket[a["from_bucket_id"]] += amt
            if month_start <= a["date"] <= month_end:
                alloc_month_to[a["to_bucket_id"]] += amt
                alloc_month_from[a["from_bucket_id"]] += amt
            if a["date"] < month_start:
                alloc_pre_to[a["to_bucket_id"]] += amt
                alloc_pre_from[a["from_bucket_id"]] += amt

        results = []
        for category in categories:
            category = self._decode_json_fields(category, {"metadata"})
            if category["is_hidden"] and not show_hidden:
                continue
            cid = category["category_id"]
            bucket_id = self._bucket_id_for_category(cid)
            metadata = cast(dict[str, Any], category.get("metadata") or {})
            category_links = link_behaviors.get(cid, [])
            category_link = category_links[0] if category_links else None
            has_transfer_in_link = any(
                link["derivation_method"] == DERIVATION_METHOD_TRANSFER_IN_ONLY
                for link in category_links
            )
            is_cc = category["category_kind"] == CATEGORY_KIND_CREDIT_CARD_PAYMENT

            if (
                is_cc
                and category_link is not None
                and category_link["derivation_method"] == DERIVATION_METHOD_CC_SPEND_AND_TRANSFER
            ):
                # Credit card payment category: alloc balance + derived CC activity
                available = (
                    alloc_to_bucket.get(bucket_id, 0)
                    - alloc_from_bucket.get(bucket_id, 0)
                    + link_derived_by_cat.get(cid, 0)
                )
            elif has_transfer_in_link:
                # Linked category (investment/loan): tx + alloc - derived transfer-in
                available = (
                    tx_by_category.get(cid, 0)
                    + alloc_to_bucket.get(bucket_id, 0)
                    - alloc_from_bucket.get(bucket_id, 0)
                    - link_derived_by_cat.get(cid, 0)
                )
            else:
                # Unlinked category or context-only link: tx + alloc
                available = (
                    tx_by_category.get(cid, 0)
                    + alloc_to_bucket.get(bucket_id, 0)
                    - alloc_from_bucket.get(bucket_id, 0)
                )

            month_activity = tx_month_activity.get(cid, 0) + link_derived_month_by_cat.get(cid, 0)
            month_budgeted = alloc_month_to.get(bucket_id, 0) - alloc_month_from.get(bucket_id, 0)
            starting_available = (
                tx_pre_month.get(cid, 0)
                + alloc_pre_to.get(bucket_id, 0)
                - alloc_pre_from.get(bucket_id, 0)
                + link_derived_pre_month_by_cat.get(cid, 0)
            )

            monthly_funding = self._compute_monthly_funding(category)

            results.append(
                category
                | {
                    "bucket_id": bucket_id,
                    "group_name": groups[category["group_id"]]["name"],
                    "available_minor": available,
                    "month_activity_minor": month_activity,
                    "month_budgeted_minor": month_budgeted,
                    "starting_available_minor": starting_available,
                    "monthly_funding_minor": monthly_funding,
                    "linked_account_id": linked_account_id_by_cat.get(cid),
                    "icon": metadata.get("icon"),
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

    def list_category_activity(self) -> list[dict[str, Any]]:
        return self.db.fetch_all(load_sql("queries/category_activity"))

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
            "groups": self.list_category_groups(
                month=month, show_hidden=show_hidden, precomputed_categories=categories
            ),
            "unconfigured_goal_count": sum(
                1
                for c in categories
                if c["category_kind"] == CATEGORY_KIND_STANDARD and c.get("goal_type") is None
            ),
        }

    def get_net_worth(self) -> dict[str, Any]:
        accounts = {
            row["account_id"]: row
            for row in self.db.fetch_all(load_sql("queries/current_accounts"))
        }
        valuations = [
            self._decode_json_fields(row, {"metadata"})
            for row in self.db.fetch_all(load_sql("queries/current_net_worth_valuations_ordered"))
        ]
        latest_valuation_by_account: dict[str, dict[str, Any]] = {}
        for valuation in valuations:
            account_id = valuation["account_id"] or valuation["raw_name"]
            latest_valuation_by_account.setdefault(account_id, valuation)

        total = 0
        items = []
        for account in self.list_accounts(show_hidden=True):
            if not account["is_active"]:
                continue
            amount = int(account["net_worth_contribution_minor"])
            total += amount
            if account["account_class"] == ACCOUNT_CLASS_LOAN:
                liability = int(account.get("liability_component_minor", 0))
                escrow = int(account.get("restricted_asset_component_minor", 0))
                unapplied = int(account.get("unapplied_credit_component_minor", 0))
                items.append(
                    account
                    | {
                        "account_name": account["name"],
                        "net_worth_minor": liability,
                        "source": account["value_source"],
                        "component_kind": "LOAN_LIABILITY",
                        "ignored_import_value": False,
                        "ignored_reason": None,
                        "match_candidates": [],
                    }
                )
                for component_kind, component_name, component_amount in (
                    ("ESCROW", f"{account['name']} escrow", escrow),
                    (
                        "UNAPPLIED_CREDIT",
                        f"{account['name']} unapplied credit",
                        unapplied,
                    ),
                ):
                    if component_amount:
                        items.append(
                            account
                            | {
                                "presentation_id": f"{account['account_id']}:{component_kind}",
                                "account_name": component_name,
                                "net_worth_minor": component_amount,
                                "source": account["value_source"],
                                "component_kind": component_kind,
                                "ignored_import_value": False,
                                "ignored_reason": None,
                                "match_candidates": [],
                            }
                        )
                continue
            items.append(
                account
                | {
                    "account_name": account["name"],
                    "net_worth_minor": amount,
                    "source": account["value_source"],
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
            # Non-budget valuations are already represented by the account's
            # type-aware value item above.
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
        now = self.clock.now()
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

    def move_allocation(
        self,
        *,
        client_operation_id: str,
        from_bucket_id: str,
        to_bucket_id: str,
        amount_minor: int,
        memo: str,
        allocation_date: date,
    ) -> dict[str, Any]:
        if amount_minor <= 0:
            raise ValueError("Allocation amount must be positive")
        if from_bucket_id == to_bucket_id:
            raise ValueError("Move requires distinct buckets")
        now = self.clock.now()
        request = {
            "from_bucket_id": from_bucket_id,
            "to_bucket_id": to_bucket_id,
            "amount_minor": amount_minor,
            "memo": memo,
            "date": allocation_date,
        }

        def apply_move(connection: duckdb.DuckDBPyConnection, _fingerprint: str) -> dict[str, Any]:
            for bucket_id in (from_bucket_id, to_bucket_id):
                if (
                    connection.execute(
                        load_sql("queries/current_allocatable_budget_bucket_by_id"),
                        (bucket_id,),
                    ).fetchone()
                    is None
                ):
                    raise ValueError("Move requires active allocatable buckets")
            allocation_id = str(uuid4())
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

        return execute_financial_command(
            self.db,
            client_operation_id=client_operation_id,
            command_kind="MOVE_ALLOCATION",
            request=request,
            command=apply_move,
            now=now,
        )

    def fund_category(
        self,
        *,
        client_operation_id: str,
        category_id: str,
        amount_minor: int,
        memo: str,
        allocation_date: date,
    ) -> dict[str, Any]:
        if amount_minor <= 0:
            raise ValueError("Funding amount must be positive")
        now = self.clock.now()
        request = {
            "category_id": category_id,
            "amount_minor": amount_minor,
            "memo": memo,
            "date": allocation_date,
        }

        def apply_funding(
            connection: duckdb.DuckDBPyConnection, _fingerprint: str
        ) -> dict[str, Any]:
            category_cursor = connection.execute(
                load_sql("queries/current_category_by_id"),
                (category_id,),
            )
            category_row = category_cursor.fetchone()
            if category_row is None:
                raise ValueError("Category not found")
            category = dict(
                zip(
                    [column[0] for column in category_cursor.description],
                    category_row,
                    strict=True,
                )
            )
            if not category["is_active"] or category["category_kind"] != CATEGORY_KIND_STANDARD:
                raise ValueError("Funding requires an active standard category")

            bucket = connection.execute(
                load_sql("queries/current_allocatable_budget_bucket_by_category"),
                (category_id,),
            ).fetchone()
            if bucket is None:
                raise ValueError("Category does not have an allocatable budget bucket")

            allocation_id = str(uuid4())
            insert_version(
                connection,
                "allocations",
                {
                    "allocation_id": allocation_id,
                    "date": allocation_date,
                    "from_bucket_id": str(SYSTEM_ATB_BUCKET_ID),
                    "to_bucket_id": str(bucket[0]),
                    "amount_minor": amount_minor,
                    "memo": memo,
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
            return {"allocation_id": allocation_id}

        return execute_financial_command(
            self.db,
            client_operation_id=client_operation_id,
            command_kind="FUND_CATEGORY",
            request=request,
            command=apply_funding,
            now=now,
        )

    def fund_group(
        self,
        *,
        client_operation_id: str,
        group_id: str,
        items: list[dict[str, Any]],
        allocation_date: date,
    ) -> dict[str, Any]:
        category_ids = [str(item["category_id"]) for item in items]
        if len(category_ids) != len(set(category_ids)):
            raise ValueError("Group funding categories must be unique")
        now = self.clock.now()
        request = {
            "group_id": group_id,
            "items": items,
            "date": allocation_date,
        }

        def apply_group_funding(
            connection: duckdb.DuckDBPyConnection, _fingerprint: str
        ) -> dict[str, Any]:
            planned: list[tuple[dict[str, Any], int, str]] = []
            for item in items:
                cursor = connection.execute(
                    load_sql("queries/current_category_by_id"),
                    (item["category_id"],),
                )
                row = cursor.fetchone()
                if row is None:
                    raise ValueError("Group funding category not found")
                category = dict(zip([column[0] for column in cursor.description], row, strict=True))
                if (
                    str(category["group_id"]) != group_id
                    or not category["is_active"]
                    or category["is_hidden"]
                    or category["category_kind"] != CATEGORY_KIND_STANDARD
                ):
                    raise ValueError(
                        "Group funding requires active categories in the selected group"
                    )
                bucket = connection.execute(
                    load_sql("queries/current_allocatable_budget_bucket_by_category"),
                    (item["category_id"],),
                ).fetchone()
                if bucket is None:
                    raise ValueError("Category does not have an allocatable budget bucket")
                planned.append((category, int(item["amount_minor"]), str(bucket[0])))

            def priority(entry: tuple[dict[str, Any], int, str]) -> tuple[Any, ...]:
                category = entry[0]
                due_date = str(category["goal_due_date"] or "9999-12-31")
                recurring_rank = 0 if category.get("goal_frequency") else 1
                discretionary_rank = 1 if category.get("goal_type") == "DISCRETIONARY" else 0
                return (
                    category["goal_due_date"] is None,
                    due_date,
                    recurring_rank,
                    discretionary_rank,
                    int(category["sort_order"]),
                    str(category["category_id"]),
                )

            remaining = max(0, int(self.compute_available_to_budget()))
            results = []
            for category, requested, bucket_id in sorted(planned, key=priority):
                funded = min(requested, remaining)
                status = "unfunded"
                allocation_id = None
                if funded > 0:
                    allocation_id = str(uuid4())
                    insert_version(
                        connection,
                        "allocations",
                        {
                            "allocation_id": allocation_id,
                            "date": allocation_date,
                            "from_bucket_id": str(SYSTEM_ATB_BUCKET_ID),
                            "to_bucket_id": bucket_id,
                            "amount_minor": funded,
                            "memo": f"Fund {category['name']}",
                            "valid_from": now,
                            "valid_to": MAX_TS,
                            "created_at": now,
                            "created_by_user_id": None,
                        },
                    )
                    remaining -= funded
                    status = "fully_funded" if funded == requested else "partially_funded"
                results.append(
                    {
                        "category_id": str(category["category_id"]),
                        "requested_minor": requested,
                        "funded_minor": funded,
                        "status": status,
                        "allocation_id": allocation_id,
                    }
                )
            return {"items": results, "remaining_available_to_budget_minor": remaining}

        return execute_financial_command(
            self.db,
            client_operation_id=client_operation_id,
            command_kind="FUND_GROUP",
            request=request,
            command=apply_group_funding,
            now=now,
        )

    def create_transaction(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = self.clock.now()
        transaction_id = str(uuid4())
        self._validate_transaction_payload(payload, new_entry=True)
        insert_after_id = payload.get("insert_after_transaction_id")
        with self.db.transaction() as connection:
            if insert_after_id is not None:
                anchor_row = connection.execute(
                    load_sql("queries/current_transaction_entry_order_by_id"),
                    (insert_after_id,),
                ).fetchone()
                if anchor_row is None:
                    raise ValueError("insert_after_transaction_id not found")
                anchor_order = int(anchor_row[0])
                connection.execute(
                    load_sql("queries/shift_transactions_entry_order_from"),
                    (anchor_order + 1, MAX_TS),
                )
                entry_order = anchor_order + 1
            else:
                max_row = connection.execute(load_sql("queries/max_entry_order")).fetchone()
                entry_order = int(max_row[0]) + 1 if max_row else 1
            record_order = (
                self._next_financial_event_order(connection)
                if payload.get("system_category") == SYSTEM_CATEGORY_TRANSFER
                else None
            )
            version = insert_version(
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
                    "entry_order": entry_order,
                    "record_order": record_order,
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
            self._insert_loan_attribution_if_applicable(
                connection,
                transaction_id=transaction_id,
                category_id=payload.get("category_id"),
                transaction_date=payload["date"],
                explicit_loan_account_id=payload.get("loan_account_id"),
                now=now,
            )
        return {"transaction_id": transaction_id, "version": version}

    def update_transaction(self, transaction_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._validate_transaction_payload(payload)
        now = self.clock.now()
        with self.db.transaction() as connection:
            cursor = connection.execute(
                load_sql("queries/current_transaction_by_id"),
                (transaction_id,),
            )
            current_row = cursor.fetchone()
            if current_row is None:
                raise TransactionNotFoundError("Transaction not found")
            current = dict(
                zip(
                    [column[0] for column in cursor.description],
                    current_row,
                    strict=True,
                )
            )
            if not close_current_version_if_expected(
                connection,
                "transactions",
                "transaction_id",
                transaction_id,
                str(payload["expected_version"]),
                now=now,
            ):
                raise TransactionVersionConflictError("Transaction version conflict")
            version = insert_version(
                connection,
                "transactions",
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
                    "entry_order": current["entry_order"],
                    "record_order": current.get("record_order"),
                    "created_at": current["created_at"],
                    "created_by_user_id": None,
                    "valid_from": now,
                    "valid_to": MAX_TS,
                },
            )
            self._insert_loan_attribution_if_applicable(
                connection,
                transaction_id=transaction_id,
                category_id=payload.get("category_id"),
                transaction_date=payload["date"],
                explicit_loan_account_id=payload.get("loan_account_id"),
                now=now,
            )
        return {"transaction_id": transaction_id, "version": version}

    def delete_transaction(self, transaction_id: str, expected_version: str) -> None:
        now = self.clock.now()
        with self.db.transaction() as connection:
            current = connection.execute(
                load_sql("queries/current_transaction_by_id"),
                (transaction_id,),
            ).fetchone()
            if current is None:
                raise TransactionNotFoundError("Transaction not found")
            if not close_current_version_if_expected(
                connection,
                "transactions",
                "transaction_id",
                transaction_id,
                expected_version,
                now=now,
            ):
                raise TransactionVersionConflictError("Transaction version conflict")

    def restore_transaction(self, transaction_id: str) -> dict[str, Any]:
        now = self.clock.now()
        with self.db.transaction() as connection:
            # Check if already has current version
            current = self.db.fetch_one(
                load_sql("queries/current_transaction_by_id"),
                (transaction_id,),
            )
            if current is not None:
                raise ValueError("Transaction already active")

            # Find latest closed version
            rows = self.db.fetch_all(
                render_sql(
                    "templates/select_columns_where_ordered",
                    columns="*",
                    table="transactions",
                    predicate="transaction_id = ? AND valid_to != ?",
                    order_by="valid_to DESC",
                ),
                (transaction_id, MAX_TS),
            )
            if not rows:
                raise ValueError("Transaction not found or not deleted")

            latest_closed = rows[0]
            version = insert_version(
                connection,
                "transactions",
                {
                    "transaction_id": transaction_id,
                    "date": latest_closed["date"],
                    "account_id": latest_closed["account_id"],
                    "amount_minor": latest_closed["amount_minor"],
                    "category_id": latest_closed["category_id"],
                    "system_category": latest_closed["system_category"],
                    "status": latest_closed["status"],
                    "memo": latest_closed["memo"],
                    "entry_order": latest_closed["entry_order"],
                    "record_order": latest_closed.get("record_order"),
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": latest_closed["created_at"],
                    "created_by_user_id": latest_closed["created_by_user_id"],
                },
            )
        return {"transaction_id": transaction_id, "version": version}

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
        self._require_distinct_accounts(from_account_id, to_account_id)
        now = self.clock.now()
        with self.db.transaction() as connection:
            return self._insert_transfer(
                connection,
                from_account_id=from_account_id,
                to_account_id=to_account_id,
                amount_minor=amount_minor,
                transfer_date=transfer_date,
                memo=memo,
                status=status,
                now=now,
            )

    def list_account_budget_links(self, account_id: str) -> list[dict[str, Any]]:
        self._require_account(account_id)
        return self.db.fetch_all(
            load_sql("queries/current_account_budget_links_by_account"),
            (account_id,),
        )

    def set_account_budget_link(self, account_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        account = self._require_account(account_id)
        behavior = payload["link_behavior"]
        allowed_class = {
            LINK_BEHAVIOR_CREDIT_CARD_PAYMENT: ACCOUNT_CLASS_BUDGET,
            LINK_BEHAVIOR_INVESTMENT_CONTRIBUTION: ACCOUNT_CLASS_INVESTMENT,
            "LOAN_PAYMENT": ACCOUNT_CLASS_LOAN,
        }[behavior]
        if account["account_class"] != allowed_class:
            raise ValueError(f"{behavior} is not valid for this account class")
        if (
            self.db.fetch_one(load_sql("queries/current_category_by_id"), (payload["category_id"],))
            is None
        ):
            raise ValueError("Category not found")
        now = self.clock.now()
        with self.db.transaction() as connection:
            connection.execute(
                load_sql("queries/close_account_budget_links_by_account_behavior"),
                (now, account_id, behavior),
            )
            self._create_account_budget_link(
                connection,
                account_id,
                payload["category_id"],
                behavior,
                DERIVATION_METHOD_TRANSFER_IN_ONLY,
                now,
                effective_date=payload["effective_date"],
            )
        return {"account_id": account_id, "link_behavior": behavior}

    def create_investment_transfer(
        self, investment_account_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        self._require_account_class(investment_account_id, ACCOUNT_CLASS_INVESTMENT)
        return self._create_rich_account_operation(
            endpoint_account_id=investment_account_id,
            payload=payload,
            operation_kind=f"INVESTMENT_{payload['direction']}",
        )

    def create_credit_card_payment(
        self, credit_card_account_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        self._require_account_class(credit_card_account_id, ACCOUNT_CLASS_BUDGET)
        return self._create_rich_account_operation(
            endpoint_account_id=credit_card_account_id,
            payload=payload,
            operation_kind="CREDIT_CARD_PAYMENT",
        )

    def create_account(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = self.clock.now()
        opening_valuation_date = None
        if payload.get("opening_valuation_minor") is not None:
            opening_valuation_date = self._non_future_date(
                payload.get("opening_valuation_date", now.date()),
                field_name="Opening valuation date",
            )
        opening_loan_date = None
        if payload.get("current_principal_minor") is not None:
            opening_loan_date = self._non_future_date(
                payload["current_principal_as_of"],
                field_name="Current principal as-of date",
            )
        configured_category_id = (
            payload.get("investment_contribution_category_id")
            if payload["account_class"] == ACCOUNT_CLASS_INVESTMENT
            else payload.get("loan_payment_category_id")
            if payload["account_class"] == ACCOUNT_CLASS_LOAN
            else None
        )
        if (
            configured_category_id is not None
            and self.db.fetch_one(
                load_sql("queries/current_category_by_id"), (configured_category_id,)
            )
            is None
        ):
            raise ValueError("Category not found")
        account_id = str(uuid4())
        with self.db.transaction() as connection:
            insert_version(
                connection,
                "accounts",
                {
                    "account_id": account_id,
                    "account_class": payload["account_class"],
                    "name": payload["name"],
                    "institution": payload.get("institution"),
                    "account_number_last4": payload.get("account_number_last4"),
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
                if budget_account_type == BUDGET_ACCOUNT_TYPE_CREDIT_CARD:
                    payment_category_id = self._create_credit_card_payment_category(
                        connection, payload["name"], now
                    )
                    self._create_account_budget_link(
                        connection,
                        account_id,
                        payment_category_id,
                        LINK_BEHAVIOR_CREDIT_CARD_PAYMENT,
                        DERIVATION_METHOD_CC_SPEND_AND_TRANSFER,
                        now,
                    )
                insert_version(
                    connection,
                    "budget_account_settings",
                    {
                        "account_id": account_id,
                        "budget_account_type": budget_account_type,
                        "display_liability_positive": payload.get(
                            "display_liability_positive",
                            budget_account_type == BUDGET_ACCOUNT_TYPE_CREDIT_CARD,
                        ),
                        "apy_minor": payload.get("apy_minor"),
                        "valid_from": now,
                        "valid_to": MAX_TS,
                        "created_at": now,
                        "created_by_user_id": None,
                    },
                )
            elif payload["account_class"] == ACCOUNT_CLASS_TRACKING:
                insert_version(
                    connection,
                    "tracking_account_details",
                    {
                        "account_id": account_id,
                        "polarity": payload.get("polarity", "ASSET"),
                        "source": payload.get("source"),
                        "apy_minor": payload.get("apy_minor"),
                        "valid_from": now,
                        "valid_to": MAX_TS,
                        "created_at": now,
                        "created_by_user_id": None,
                    },
                )
            elif payload["account_class"] == ACCOUNT_CLASS_INVESTMENT:
                insert_version(
                    connection,
                    "investment_account_details",
                    {
                        "account_id": account_id,
                        "self_managed": payload.get("self_managed", False),
                        "tax_treatment": payload.get("tax_treatment", "TAXABLE_BROKERAGE"),
                        "valid_from": now,
                        "valid_to": MAX_TS,
                        "created_at": now,
                        "created_by_user_id": None,
                    },
                )
                if configured_category_id is not None:
                    self._create_account_budget_link(
                        connection,
                        account_id,
                        configured_category_id,
                        LINK_BEHAVIOR_INVESTMENT_CONTRIBUTION,
                        DERIVATION_METHOD_TRANSFER_IN_ONLY,
                        now,
                    )
            elif payload["account_class"] == ACCOUNT_CLASS_LOAN:
                insert_version(
                    connection,
                    "loan_details",
                    {
                        "account_id": account_id,
                        "original_amount_minor": payload.get("original_amount_minor"),
                        "origination_date": payload.get("origination_date"),
                        "rate_minor": payload.get("rate_minor"),
                        "rate_type": payload.get("rate_type"),
                        "scheduled_principal_interest_minor": payload.get(
                            "scheduled_principal_interest_minor"
                        ),
                        "payment_frequency": payload.get("payment_frequency"),
                        "next_payment_date": payload.get("next_payment_date"),
                        "maturity_date": payload.get("maturity_date"),
                        "remaining_term_months": payload.get("remaining_term_months"),
                        "recurring_extra_principal_minor": payload.get(
                            "recurring_extra_principal_minor"
                        ),
                        "status": payload.get("status", "IN_REPAYMENT"),
                        "valid_from": now,
                        "valid_to": MAX_TS,
                        "created_at": now,
                        "created_by_user_id": None,
                    },
                )
                if opening_loan_date is not None:
                    insert_version(
                        connection,
                        "loan_balance_snapshots",
                        {
                            "snapshot_id": str(uuid4()),
                            "account_id": account_id,
                            "effective_date": opening_loan_date,
                            "principal_balance_minor": abs(payload["current_principal_minor"]),
                            "accrued_interest_minor": None,
                            "escrow_balance_minor": 0,
                            "unapplied_credit_minor": None,
                            "ytd_principal_paid_minor": None,
                            "ytd_interest_paid_minor": None,
                            "attributed_payment_minor": 0,
                            "principal_reduction_minor": 0,
                            "unknown_nonprincipal_minor": 0,
                            "notes": "Opening current principal",
                            "valid_from": now,
                            "valid_to": MAX_TS,
                            "created_at": now,
                            "created_by_user_id": None,
                        },
                    )
                if configured_category_id is not None:
                    self._create_account_budget_link(
                        connection,
                        account_id,
                        configured_category_id,
                        LINK_BEHAVIOR_LOAN_PAYMENT,
                        DERIVATION_METHOD_TRANSFER_IN_ONLY,
                        now,
                        effective_date=opening_loan_date,
                    )
            elif payload["account_class"] == ACCOUNT_CLASS_TANGIBLE_ASSET:
                if payload.get("opening_valuation_minor") is not None:
                    insert_version(
                        connection,
                        "tangible_asset_valuations",
                        {
                            "valuation_id": str(uuid4()),
                            "account_id": account_id,
                            "effective_date": opening_valuation_date,
                            "amount_minor": payload["opening_valuation_minor"],
                            "source": payload.get("source", "manual"),
                            "notes": "Opening valuation",
                            "valid_from": now,
                            "valid_to": MAX_TS,
                            "created_at": now,
                            "created_by_user_id": None,
                        },
                    )
        return {"account_id": account_id}

    def create_tracking_cutover(
        self, predecessor_account_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        now = self.clock.now()

        def apply_cutover(
            connection: duckdb.DuckDBPyConnection, request_fingerprint: str
        ) -> dict[str, Any]:
            return self._create_tracking_cutover_in_transaction(
                connection,
                predecessor_account_id,
                payload,
                request_fingerprint=request_fingerprint,
                now=now,
            )

        return execute_financial_command(
            self.db,
            client_operation_id=payload["operation_id"],
            command_kind="TRACKING_CUTOVER",
            request={"predecessor_account_id": predecessor_account_id} | payload,
            command=apply_cutover,
            now=now,
        )

    def _create_tracking_cutover_in_transaction(
        self,
        connection: duckdb.DuckDBPyConnection,
        predecessor_account_id: str,
        payload: dict[str, Any],
        *,
        request_fingerprint: str,
        now: datetime,
    ) -> dict[str, Any]:
        operation_id = str(payload["operation_id"])
        predecessor = self.db.fetch_one(
            load_sql("queries/current_account_by_id"), (predecessor_account_id,)
        )
        if predecessor is None or predecessor["account_class"] != ACCOUNT_CLASS_TRACKING:
            raise ValueError("Cutover predecessor must be a tracking account")
        if (
            self.db.fetch_one(
                load_sql("queries/tracking_cutover_by_predecessor"), (predecessor_account_id,)
            )
            is not None
        ):
            raise ValueError("Tracking account already has a cutover")

        cutover_date = payload["cutover_date"]
        if isinstance(cutover_date, str):
            cutover_date = date.fromisoformat(cutover_date)
        tracking_details = self.db.fetch_one(
            load_sql("queries/current_tracking_account_details_by_account"),
            (predecessor_account_id,),
        )
        prior_snapshot = self.db.fetch_one(
            load_sql("queries/latest_tracking_valuation_for_account_through_date"),
            (predecessor_account_id, cutover_date),
        )
        if tracking_details is None or prior_snapshot is None:
            raise ValueError("Tracking account needs a snapshot at or before cutover")
        prior_amount = abs(int(prior_snapshot["amount_minor"]))
        if prior_amount != int(payload["expected_predecessor_value_minor"]):
            raise ValueError("Tracking value changed; review the cutover again")

        successor_values: list[int] = []
        for successor in payload["successors"]:
            if not str(successor.get("name", "")).strip():
                raise ValueError("Cutover successor name is required")
            if successor["account_class"] == ACCOUNT_CLASS_LOAN and not successor.get(
                "payment_category_id"
            ):
                raise ValueError("Loan successor requires a payment category")
            if successor["account_class"] == ACCOUNT_CLASS_INVESTMENT:
                tickers = [holding["ticker"].strip().upper() for holding in successor["holdings"]]
                if len(tickers) != len(set(tickers)):
                    raise ValueError("Cutover investment holdings must use unique tickers")
            category_id = successor.get("contribution_category_id") or successor.get(
                "payment_category_id"
            )
            if category_id is not None:
                category = self.db.fetch_one(
                    load_sql("queries/current_category_by_id"), (category_id,)
                )
                if (
                    category is None
                    or not category["is_active"]
                    or category["category_kind"] != CATEGORY_KIND_STANDARD
                ):
                    raise ValueError("Cutover links require an active standard category")
            successor_values.append(self._cutover_successor_value(successor))

        successor_total = sum(successor_values)
        predecessor_is_liability = tracking_details["polarity"] == "LIABILITY"
        final_predecessor_amount = int(payload["final_predecessor_value_minor"])
        signed_final_predecessor = (
            -final_predecessor_amount if predecessor_is_liability else final_predecessor_amount
        )
        if successor_total != signed_final_predecessor:
            raise ValueError("Successor total must equal the final tracking value")

        existing_final = self.db.fetch_one(
            load_sql("queries/current_tracking_valuation_by_account_date"),
            (predecessor_account_id, cutover_date),
        )
        final_valuation_id = (
            str(existing_final["valuation_id"])
            if existing_final is not None
            else str(uuid5(NAMESPACE_URL, f"dojo:cutover:{operation_id}:predecessor"))
        )
        successor_ids = [
            str(uuid5(NAMESPACE_URL, f"dojo:cutover:{operation_id}:successor:{index}"))
            for index in range(len(payload["successors"]))
        ]
        final_values = {
            "valuation_id": final_valuation_id,
            "account_id": predecessor_account_id,
            "raw_name": existing_final["raw_name"] if existing_final else "",
            "effective_date": cutover_date,
            "amount_minor": final_predecessor_amount,
            "notes": "Final tracking value at representation cutover",
            "metadata": json_dumps({"source": "cutover", "operation_id": operation_id}),
            "created_at": existing_final["created_at"] if existing_final else now,
            "created_by_user_id": None,
        }
        if existing_final is not None:
            replace_current_version(
                connection,
                "net_worth_valuations",
                "valuation_id",
                final_valuation_id,
                {"row_id": str(uuid4())} | final_values,
                now=now,
            )
        else:
            insert_version(
                connection,
                "net_worth_valuations",
                final_values | {"valid_from": now, "valid_to": MAX_TS},
            )

        for index, (successor, successor_id, opening_value) in enumerate(
            zip(payload["successors"], successor_ids, successor_values, strict=True)
        ):
            self._insert_cutover_successor(
                connection,
                operation_id=operation_id,
                successor_order=index,
                successor_id=successor_id,
                successor=successor,
                cutover_date=cutover_date,
                opening_net_worth_minor=opening_value,
                now=now,
            )

        connection.execute(
            load_sql("queries/insert_tracking_cutover"),
            (
                operation_id,
                predecessor_account_id,
                cutover_date,
                signed_final_predecessor,
                successor_total,
                final_valuation_id,
                request_fingerprint,
                now,
            ),
        )

        cutover = self.db.fetch_one(
            load_sql("queries/tracking_cutover_by_operation"), (operation_id,)
        )
        assert cutover is not None
        return self._tracking_cutover_response(cutover)

    def update_account(self, account_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.db.fetch_one(
            load_sql("queries/current_account_by_id"),
            (account_id,),
        )
        if current is None:
            raise ValueError("Account not found")
        now = self.clock.now()
        account_class = current["account_class"]
        with self.db.transaction() as connection:
            replace_current_version(
                connection,
                "accounts",
                "account_id",
                account_id,
                {
                    "row_id": str(uuid4()),
                    "account_id": account_id,
                    "account_class": account_class,
                    "name": payload.get("name", current["name"]),
                    "institution": payload.get("institution", current.get("institution")),
                    "account_number_last4": payload.get(
                        "account_number_last4", current.get("account_number_last4")
                    ),
                    "is_hidden": payload.get("is_hidden", current["is_hidden"]),
                    "is_active": payload.get("is_active", current["is_active"]),
                    "metadata": current["metadata"],
                    "created_at": current["created_at"],
                    "created_by_user_id": current["created_by_user_id"],
                },
                now=now,
            )
            if account_class == ACCOUNT_CLASS_BUDGET:
                budget_current = self.db.fetch_one(
                    load_sql("queries/current_budget_account_settings_by_account"),
                    (account_id,),
                )
                if budget_current is not None:
                    replace_current_version(
                        connection,
                        "budget_account_settings",
                        "account_id",
                        account_id,
                        {
                            "row_id": str(uuid4()),
                            "account_id": account_id,
                            "budget_account_type": budget_current["budget_account_type"],
                            "display_liability_positive": budget_current[
                                "display_liability_positive"
                            ],
                            "apy_minor": payload.get("apy_minor", budget_current.get("apy_minor")),
                            "created_at": budget_current["created_at"],
                            "created_by_user_id": budget_current["created_by_user_id"],
                        },
                        now=now,
                    )
            elif account_class == ACCOUNT_CLASS_TRACKING:
                tracking_current = self.db.fetch_one(
                    load_sql("queries/current_tracking_account_details_by_account"),
                    (account_id,),
                )
                if tracking_current is not None:
                    replace_current_version(
                        connection,
                        "tracking_account_details",
                        "account_id",
                        account_id,
                        {
                            "row_id": str(uuid4()),
                            "account_id": account_id,
                            "polarity": payload.get("polarity", tracking_current["polarity"]),
                            "source": payload.get("source", tracking_current.get("source")),
                            "apy_minor": payload.get(
                                "apy_minor", tracking_current.get("apy_minor")
                            ),
                            "created_at": tracking_current["created_at"],
                            "created_by_user_id": tracking_current["created_by_user_id"],
                        },
                        now=now,
                    )
            elif account_class == ACCOUNT_CLASS_INVESTMENT:
                inv_current = self.db.fetch_one(
                    load_sql("queries/current_investment_account_details_by_account"),
                    (account_id,),
                )
                if inv_current is not None:
                    replace_current_version(
                        connection,
                        "investment_account_details",
                        "account_id",
                        account_id,
                        {
                            "row_id": str(uuid4()),
                            "account_id": account_id,
                            "self_managed": payload.get(
                                "self_managed", inv_current.get("self_managed")
                            ),
                            "tax_treatment": payload.get(
                                "tax_treatment", inv_current.get("tax_treatment")
                            ),
                            "created_at": inv_current["created_at"],
                            "created_by_user_id": inv_current["created_by_user_id"],
                        },
                        now=now,
                    )
            elif account_class == ACCOUNT_CLASS_LOAN:
                loan_current = self.db.fetch_one(
                    load_sql("queries/current_loan_details_by_account"),
                    (account_id,),
                )
                if loan_current is not None:
                    replace_current_version(
                        connection,
                        "loan_details",
                        "account_id",
                        account_id,
                        {
                            "row_id": str(uuid4()),
                            "account_id": account_id,
                            "original_amount_minor": payload.get(
                                "original_amount_minor", loan_current.get("original_amount_minor")
                            ),
                            "origination_date": payload.get(
                                "origination_date", loan_current.get("origination_date")
                            ),
                            "rate_minor": payload.get("rate_minor", loan_current.get("rate_minor")),
                            "rate_type": payload.get("rate_type", loan_current.get("rate_type")),
                            "scheduled_principal_interest_minor": payload.get(
                                "scheduled_principal_interest_minor",
                                loan_current.get("scheduled_principal_interest_minor"),
                            ),
                            "payment_frequency": payload.get(
                                "payment_frequency", loan_current.get("payment_frequency")
                            ),
                            "next_payment_date": payload.get(
                                "next_payment_date", loan_current.get("next_payment_date")
                            ),
                            "maturity_date": payload.get(
                                "maturity_date", loan_current.get("maturity_date")
                            ),
                            "remaining_term_months": payload.get(
                                "remaining_term_months", loan_current.get("remaining_term_months")
                            ),
                            "recurring_extra_principal_minor": payload.get(
                                "recurring_extra_principal_minor",
                                loan_current.get("recurring_extra_principal_minor"),
                            ),
                            "status": payload.get("loan_status", loan_current.get("status")),
                            "created_at": loan_current["created_at"],
                            "created_by_user_id": loan_current["created_by_user_id"],
                        },
                        now=now,
                    )
        return {"account_id": account_id}

    def create_investment_position(
        self, account_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        self._require_account_class(account_id, ACCOUNT_CLASS_INVESTMENT)
        effective_date = self._non_future_date(payload["effective_date"])
        now = self.clock.now()
        position_id = str(uuid4())
        with self.db.transaction() as connection:
            insert_version(
                connection,
                "investment_positions",
                {
                    "position_id": position_id,
                    "account_id": account_id,
                    "ticker": payload["ticker"].strip().upper(),
                    "effective_date": effective_date,
                    "quantity_micros": payload["quantity_micros"],
                    "average_basis_minor": payload["average_basis_minor"],
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
        return {"position_id": position_id}

    def list_investment_positions(self, account_id: str) -> list[dict[str, Any]]:
        return self.db.fetch_all(
            load_sql("queries/current_investment_positions_by_account"),
            (account_id,),
        )

    def create_investment_cash_snapshot(
        self, account_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        self._require_account_class(account_id, ACCOUNT_CLASS_INVESTMENT)
        effective_date = self._non_future_date(payload["effective_date"])
        now = self.clock.now()
        snapshot_id = str(uuid4())
        with self.db.transaction() as connection:
            record_order = self._next_financial_event_order(connection)
            insert_version(
                connection,
                "investment_cash_snapshots",
                {
                    "snapshot_id": snapshot_id,
                    "account_id": account_id,
                    "effective_date": effective_date,
                    "cash_balance_minor": payload["cash_balance_minor"],
                    "record_order": record_order,
                    "notes": payload.get("notes", ""),
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
        return {"snapshot_id": snapshot_id}

    def list_investment_cash_snapshots(self, account_id: str) -> list[dict[str, Any]]:
        return self.db.fetch_all(
            load_sql("queries/current_investment_cash_snapshots_by_account"),
            (account_id,),
        )

    def create_investment_price_snapshot(self, payload: dict[str, Any]) -> dict[str, Any]:
        effective_date = self._non_future_date(payload["effective_date"])
        now = self.clock.now()
        snapshot_id = str(uuid4())
        with self.db.transaction() as connection:
            insert_version(
                connection,
                "investment_price_snapshots",
                {
                    "snapshot_id": snapshot_id,
                    "account_id": payload.get("account_id"),
                    "ticker": payload["ticker"].strip().upper(),
                    "effective_date": effective_date,
                    "price_minor": payload["price_minor"],
                    "source": payload.get("source", "manual"),
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
        return {"snapshot_id": snapshot_id}

    def list_investment_price_snapshots(self, ticker: str) -> list[dict[str, Any]]:
        return self.db.fetch_all(
            load_sql("queries/current_investment_price_snapshots_by_ticker"),
            (ticker.strip().upper(),),
        )

    def reconcile_investment_statement(
        self, account_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        self._require_account_class(account_id, ACCOUNT_CLASS_INVESTMENT)
        effective_date = self._non_future_date(payload["effective_date"])
        now = self.clock.now()
        existing_positions = self.db.fetch_all(
            load_sql("queries/current_investment_positions_by_account_date"),
            (account_id, effective_date),
        )
        existing_positions_by_ticker = {row["ticker"]: row for row in existing_positions}
        existing_cash = self.db.fetch_one(
            load_sql("queries/current_investment_cash_by_account_date"),
            (account_id, effective_date),
        )

        with self.db.transaction() as connection:
            record_order = self._next_financial_event_order(connection)
            for existing_position in existing_positions:
                close_current_version(
                    connection,
                    "investment_positions",
                    "position_id",
                    str(existing_position["position_id"]),
                    now=now,
                )
            for holding in payload["holdings"]:
                ticker = holding["ticker"].strip().upper()
                matched_position = existing_positions_by_ticker.get(ticker)
                insert_version(
                    connection,
                    "investment_positions",
                    {
                        "position_id": (
                            str(matched_position["position_id"])
                            if matched_position
                            else str(uuid4())
                        ),
                        "account_id": account_id,
                        "ticker": ticker,
                        "effective_date": effective_date,
                        "quantity_micros": holding["quantity_micros"],
                        "average_basis_minor": holding["average_basis_minor"],
                        "valid_from": now,
                        "valid_to": MAX_TS,
                        "created_at": (matched_position["created_at"] if matched_position else now),
                        "created_by_user_id": None,
                    },
                )
                self._replace_statement_price(
                    connection,
                    account_id=account_id,
                    ticker=ticker,
                    effective_date=effective_date,
                    price_minor=holding["price_minor"],
                    now=now,
                )

            cash_id = str(existing_cash["snapshot_id"]) if existing_cash else str(uuid4())
            if existing_cash:
                close_current_version(
                    connection,
                    "investment_cash_snapshots",
                    "snapshot_id",
                    cash_id,
                    now=now,
                )
            insert_version(
                connection,
                "investment_cash_snapshots",
                {
                    "snapshot_id": cash_id,
                    "account_id": account_id,
                    "effective_date": effective_date,
                    "cash_balance_minor": payload["cash_balance_minor"],
                    "record_order": record_order,
                    "notes": payload.get("notes", ""),
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": existing_cash["created_at"] if existing_cash else now,
                    "created_by_user_id": None,
                },
            )
        return {"effective_date": str(effective_date)}

    def latest_investment_statement(self, account_id: str) -> dict[str, Any]:
        self._require_account_class(account_id, ACCOUNT_CLASS_INVESTMENT)
        as_of = self.clock.today()
        cash = self._rows_by_account("queries/latest_investment_cash_through_date", as_of).get(
            account_id
        )
        if cash is None:
            return {
                "effective_date": None,
                "cash_balance_minor": None,
                "holdings": [],
                "holdings_value_minor": None,
                "holdings_cost_basis_minor": None,
                "unrealized_gain_minor": None,
                "current_value_minor": None,
                "provisional_transfer_minor": 0,
            }
        effective_date = cash["effective_date"]
        holdings = []
        holdings_value = 0
        holdings_cost_basis = 0
        for position in self.db.fetch_all(
            load_sql("queries/current_investment_positions_by_account_date"),
            (account_id, effective_date),
        ):
            price = self.db.fetch_one(
                load_sql("queries/current_investment_price_by_ticker_date"),
                (account_id, position["ticker"], effective_date, account_id),
            )
            if price is None:
                raise ValueError(f"Missing statement price for {position['ticker']}")
            if position["average_basis_minor"] is None:
                raise ValueError(f"Missing average cost for {position['ticker']}")
            metrics = position_metrics(
                quantity_micros=int(position["quantity_micros"]),
                price_minor=int(price["price_minor"]),
                average_basis_minor=int(position["average_basis_minor"]),
            )
            holdings_value += metrics.value_minor
            holdings_cost_basis += metrics.cost_basis_minor
            holdings.append(
                position
                | {
                    "price_minor": int(price["price_minor"]),
                    "value_minor": metrics.value_minor,
                    "cost_basis_minor": metrics.cost_basis_minor,
                    "unrealized_gain_minor": metrics.unrealized_gain_minor,
                }
            )
        transfer_row = self.db.fetch_one(
            load_sql("queries/investment_transfer_delta_after_date"),
            (account_id, effective_date, effective_date, cash["record_order"], as_of),
        )
        provisional = int(transfer_row["transfer_delta_minor"] if transfer_row else 0)
        return {
            "effective_date": str(effective_date),
            "cash_balance_minor": int(cash["cash_balance_minor"]),
            "holdings": holdings,
            "holdings_value_minor": holdings_value,
            "holdings_cost_basis_minor": holdings_cost_basis,
            "unrealized_gain_minor": holdings_value - holdings_cost_basis,
            "current_value_minor": int(cash["cash_balance_minor"]) + holdings_value + provisional,
            "provisional_transfer_minor": provisional,
        }

    def create_reconciliation_draft(
        self, account_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        account = self._require_account(account_id)
        if account["account_class"] not in {ACCOUNT_CLASS_BUDGET, ACCOUNT_CLASS_INVESTMENT}:
            raise ValueError("Only budget and investment accounts can be reconciled")
        cutoff = payload["cutoff"]
        if isinstance(cutoff, str):
            cutoff = date.fromisoformat(cutoff)
        period_start = payload.get("period_start") or date.min
        if isinstance(period_start, str):
            period_start = date.fromisoformat(period_start)
        source_kind = payload["source_kind"]
        source_records = [
            SourceRecord(
                source_record_id=str(item["source_record_id"]),
                posted_date=item["posted_date"],
                cleared_date=item.get("cleared_date"),
                signed_amount_minor=(
                    -int(item["signed_amount_minor"])
                    if account.get("budget_account_type") == BUDGET_ACCOUNT_TYPE_CREDIT_CARD
                    else int(item["signed_amount_minor"])
                ),
                status=str(item["source_status"]),
                description=str(item.get("description", "")),
                transaction_id=(
                    str(item["transaction_id"]) if item.get("transaction_id") else None
                ),
            )
            for item in payload.get("source_records", [])
        ]
        evidence_id = str(uuid4())
        evidence_digest = self._source_evidence_digest(source_records)
        period_records = self._reconciliation_local_records(account_id, period_start, cutoff)
        baseline_records = self._reconciliation_local_records(account_id, date.min, cutoff)
        digest = baseline_digest(
            baseline_records,
            account_id=account_id,
            cutoff=cutoff,
            source_evidence_id=evidence_id,
            source_evidence_digest=evidence_digest,
            settings_versions=self._reconciliation_settings_versions(account_id, cutoff),
        )
        local_balance = self._reconciliation_ending_value(
            account_id=account_id,
            account_class=str(account["account_class"]),
            cutoff=cutoff,
            ledger_records=baseline_records,
        )
        ending_value = (
            -int(payload["source_ending_value_minor"])
            if account.get("budget_account_type") == BUDGET_ACCOUNT_TYPE_CREDIT_CARD
            else int(payload["source_ending_value_minor"])
        )
        reconciliation_id = str(uuid4())
        now = self.clock.now()
        with self.db.transaction() as connection:
            connection.execute(
                load_sql("queries/insert_reconciliation_commit"),
                (
                    reconciliation_id,
                    account_id,
                    account["account_class"],
                    source_kind,
                    period_start,
                    cutoff,
                    cutoff,
                    evidence_id,
                    evidence_digest,
                    digest,
                    ending_value,
                    now,
                ),
            )
            for ordinal, item in enumerate(payload.get("source_records", [])):
                record = source_records[ordinal]
                connection.execute(
                    load_sql("queries/insert_reconciliation_source_record"),
                    (
                        evidence_id,
                        record.source_record_id,
                        record.transaction_id,
                        ordinal,
                        account_id,
                        record.posted_date,
                        record.cleared_date,
                        record.signed_amount_minor,
                        record.status,
                        record.description,
                        source_digest(record),
                        json_dumps(item.get("raw_payload")),
                    ),
                )
        comparison = compare_records(period_records, source_records)
        return {
            "reconciliation_id": reconciliation_id,
            "account_id": account_id,
            "state": "DRAFT",
            "source_kind": source_kind,
            "cutoff": str(cutoff),
            "source_ending_value_minor": ending_value,
            "ledger_value_minor": local_balance,
            "difference_minor": ending_value - local_balance,
            "baseline_digest": digest,
            "classifications": comparison,
            "investment_cash_activity_minor": (
                sum(record.signed_amount_minor for record in period_records)
                if account["account_class"] == ACCOUNT_CLASS_INVESTMENT
                else 0
            ),
        }

    def apply_reconciliation(
        self, reconciliation_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        draft = self.db.fetch_one(
            load_sql("queries/reconciliation_commit_by_id"),
            (reconciliation_id,),
        )
        if draft is None:
            raise ValueError("Reconciliation not found")
        account_id = str(draft["account_id"])
        request = {"reconciliation_id": reconciliation_id, **payload}
        now = self.clock.now()

        def apply(connection: Any, _fingerprint: str) -> dict[str, Any]:
            if draft["state"] != "DRAFT":
                raise ValueError("Reconciliation is no longer a draft")
            cutoff = draft["effective_date"]
            local_records = self._reconciliation_local_records(account_id, date.min, cutoff)
            current_digest = baseline_digest(
                local_records,
                account_id=account_id,
                cutoff=cutoff,
                source_evidence_id=str(draft["source_evidence_id"]),
                source_evidence_digest=str(draft["source_evidence_digest"]),
                settings_versions=self._reconciliation_settings_versions(account_id, cutoff),
            )
            if current_digest != draft["baseline_digest"]:
                raise ValueError("Reconciliation draft is stale; create a new draft")
            ledger_value = self._reconciliation_ending_value(
                account_id=account_id,
                account_class=str(draft["account_class"]),
                cutoff=cutoff,
                ledger_records=local_records,
            )
            difference = int(draft["source_ending_value_minor"]) - ledger_value
            adjustment = payload.get("balance_adjustment_minor")
            if adjustment is not None and draft["account_class"] == ACCOUNT_CLASS_INVESTMENT:
                raise ValueError("Investment reconciliation cannot use a ledger balance adjustment")
            if difference != 0 and adjustment != difference:
                raise ValueError("Apply requires zero difference or an explicit balance adjustment")
            adjustment_id = None
            if adjustment is not None:
                adjustment_id = str(uuid4())
                insert_version(
                    connection,
                    "transactions",
                    {
                        "transaction_id": adjustment_id,
                        "date": cutoff,
                        "account_id": account_id,
                        "amount_minor": int(adjustment),
                        "category_id": None,
                        "system_category": SYSTEM_CATEGORY_BALANCE_ADJUSTMENT,
                        "status": "CLEARED",
                        "memo": "Balance adjustment from reconciliation",
                        "entry_order": int(
                            connection.execute(load_sql("queries/max_entry_order")).fetchone()[0]
                            or 0
                        )
                        + 1,
                        "record_order": self._next_financial_event_order(connection),
                        "valid_from": now,
                        "valid_to": MAX_TS,
                        "created_at": now,
                        "created_by_user_id": None,
                    },
                )
                local_records = self._reconciliation_local_records(account_id, date.min, cutoff)
            committed_digest = baseline_digest(
                local_records,
                account_id=account_id,
                cutoff=cutoff,
                source_evidence_id=str(draft["source_evidence_id"]),
                source_evidence_digest=str(draft["source_evidence_digest"]),
                settings_versions=self._reconciliation_settings_versions(account_id, cutoff),
            )
            connection.execute(
                load_sql("queries/update_reconciliation_commit_baseline"),
                (now, committed_digest, reconciliation_id),
            )
            for record in local_records:
                connection.execute(
                    load_sql("queries/insert_reconciliation_transaction_ref"),
                    (
                        reconciliation_id,
                        record.transaction_id,
                        record.valid_from,
                        account_id,
                        transaction_digest(record),
                    ),
                )
            return {
                "reconciliation_id": reconciliation_id,
                "state": "CURRENT",
                "difference_minor": 0,
                "balance_adjustment_transaction_id": adjustment_id,
            }

        return execute_financial_command(
            self.db,
            client_operation_id=payload["client_operation_id"],
            command_kind="RECONCILIATION_APPLY",
            request=request,
            command=apply,
            now=now,
        )

    def get_reconciliation(self, reconciliation_id: str) -> dict[str, Any]:
        row = self.db.fetch_one(
            load_sql("queries/reconciliation_commit_by_id"), (reconciliation_id,)
        )
        if row is None:
            raise ValueError("Reconciliation not found")
        records = self._source_records(str(row["source_evidence_id"]))
        local = self._reconciliation_local_records(
            str(row["account_id"]), row["period_start"], row["period_end"]
        )
        return row | {"source_records": records, "classifications": compare_records(local, records)}

    def list_reconciliations(self, account_id: str) -> list[dict[str, Any]]:
        self._require_account(account_id)
        return self.db.fetch_all(
            load_sql("queries/reconciliation_commits_by_account"),
            (account_id,),
        )

    def reconciliation_working_set(self, account_id: str) -> dict[str, Any]:
        self._require_account(account_id)
        latest = self.db.fetch_one(
            load_sql("queries/latest_current_reconciliation_by_account"),
            (account_id,),
        )
        if latest is None:
            return {"account_id": account_id, "state": "NOT_RECONCILED", "items": []}
        local = self._reconciliation_local_records(
            account_id, latest["period_start"], latest["period_end"]
        )
        source = self._source_records(str(latest["source_evidence_id"]))
        return {
            "account_id": account_id,
            "state": self.get_reconciliation_status(account_id),
            "items": compare_records(local, source),
        }

    def get_reconciliation_status(self, account_id: str) -> str:
        latest = self.db.fetch_one(
            load_sql("queries/latest_current_reconciliation_by_account"),
            (account_id,),
        )
        if latest is None:
            return "NOT_RECONCILED"
        local = self._reconciliation_local_records(account_id, date.min, latest["period_end"])
        digest = baseline_digest(
            local,
            account_id=account_id,
            cutoff=latest["effective_date"],
            source_evidence_id=str(latest["source_evidence_id"]),
            source_evidence_digest=str(latest["source_evidence_digest"]),
            settings_versions=self._reconciliation_settings_versions(
                account_id, latest["effective_date"]
            ),
        )
        return "CURRENT" if digest == latest["baseline_digest"] else "REOPENED"

    def _reconciliation_ending_value(
        self,
        *,
        account_id: str,
        account_class: str,
        cutoff: date,
        ledger_records: list[LocalRecord],
    ) -> int:
        if account_class != ACCOUNT_CLASS_INVESTMENT:
            return sum(record.signed_amount_minor for record in ledger_records)
        investment_value = self._investment_values(
            self.db.fetch_all(load_sql("queries/list_accounts")), cutoff
        ).get(account_id)
        if investment_value is None:
            raise ValueError("Investment account needs a statement before reconciliation")
        return int(investment_value[0])

    def _reconciliation_local_records(
        self, account_id: str, start: date, cutoff: date
    ) -> list[LocalRecord]:
        rows = self.db.fetch_all(
            load_sql("queries/current_reconciliation_transactions_for_period"),
            (account_id, start, cutoff),
        )
        return [
            LocalRecord(
                transaction_id=str(row["transaction_id"]),
                valid_from=str(row["valid_from"]),
                account_id=str(row["account_id"]),
                posted_date=row["date"],
                signed_amount_minor=int(row["amount_minor"]),
                status=str(row["status"]),
                category_id=str(row["category_id"]) if row.get("category_id") else None,
                system_category=row.get("system_category"),
                memo=str(row.get("memo") or ""),
                source_record_id=None,
            )
            for row in rows
        ]

    def _reconciliation_settings_versions(self, account_id: str, cutoff: date) -> list[str]:
        rows = self.db.fetch_all(
            load_sql("queries/budget_account_setting_version_at_date"),
            (account_id, cutoff, cutoff),
        )
        versions = [str(row["row_id"]) for row in rows]
        versions.extend(
            str(row["row_id"])
            for row in self.db.fetch_all(
                load_sql("queries/account_budget_link_version_at_date"),
                (account_id, cutoff, cutoff, cutoff),
            )
        )
        return versions

    @staticmethod
    def _source_evidence_digest(records: list[SourceRecord]) -> str:
        return sha256(
            "".join(sorted(source_digest(record) for record in records)).encode()
        ).hexdigest()

    def _source_records(self, evidence_id: str) -> list[SourceRecord]:
        return [
            SourceRecord(
                source_record_id=str(row["source_record_id"]),
                posted_date=row["posted_date"],
                cleared_date=row["cleared_date"],
                signed_amount_minor=int(row["signed_amount_minor"]),
                status=str(row["source_status"]),
                description=str(row["description"]),
                transaction_id=(str(row["transaction_id"]) if row.get("transaction_id") else None),
            )
            for row in self.db.fetch_all(
                load_sql("queries/reconciliation_source_records_by_evidence"),
                (evidence_id,),
            )
        ]

    def create_tracking_snapshot(self, account_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._require_account_class(account_id, ACCOUNT_CLASS_TRACKING)
        effective_date = self._non_future_date(payload["effective_date"])
        now = self.clock.now()
        existing = self.db.fetch_one(
            load_sql("queries/current_tracking_valuation_by_account_date"),
            (account_id, effective_date),
        )
        snapshot_id = str(existing["valuation_id"]) if existing else str(uuid4())
        values = {
            "valuation_id": snapshot_id,
            "account_id": account_id,
            "raw_name": existing["raw_name"] if existing else "",
            "effective_date": effective_date,
            "amount_minor": abs(payload["amount_minor"]),
            "notes": payload.get("notes", ""),
            "metadata": json_dumps({"source": payload.get("source", "manual")}),
            "created_at": existing["created_at"] if existing else now,
            "created_by_user_id": existing["created_by_user_id"] if existing else None,
        }
        with self.db.transaction() as connection:
            if existing:
                replace_current_version(
                    connection,
                    "net_worth_valuations",
                    "valuation_id",
                    snapshot_id,
                    {"row_id": str(uuid4())} | values,
                    now=now,
                )
            else:
                insert_version(
                    connection,
                    "net_worth_valuations",
                    values | {"valid_from": now, "valid_to": MAX_TS},
                )
        return {"valuation_id": snapshot_id}

    def list_tracking_snapshots(self, account_id: str) -> list[dict[str, Any]]:
        return self.db.fetch_all(
            load_sql("queries/current_net_worth_valuations_by_account"),
            (account_id,),
        )

    def create_loan_snapshot(self, account_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._require_account_class(account_id, ACCOUNT_CLASS_LOAN)
        now = self.clock.now()
        effective_date = self._non_future_date(payload["effective_date"])
        existing = self.db.fetch_one(
            load_sql("queries/current_loan_balance_by_account_date"),
            (account_id, effective_date),
        )
        previous = self.db.fetch_one(
            load_sql("queries/latest_loan_balance_before_date"),
            (account_id, effective_date),
        )
        snapshot_id = str(existing["snapshot_id"]) if existing else str(uuid4())
        previous_date = previous["effective_date"] if previous else effective_date
        payment_row = self.db.fetch_one(
            load_sql("queries/loan_attributed_payments_between_dates"),
            (account_id, previous_date, effective_date),
        )
        attributed_payment = int(payment_row["payment_minor"] if payment_row else 0)
        principal = abs(payload["principal_balance_minor"])
        principal_reduction = (
            max(int(previous["principal_balance_minor"]) - principal, 0) if previous else 0
        )
        unknown_nonprincipal = max(attributed_payment - principal_reduction, 0)
        values = {
            "snapshot_id": snapshot_id,
            "account_id": account_id,
            "effective_date": effective_date,
            "principal_balance_minor": principal,
            "accrued_interest_minor": (
                abs(payload["accrued_interest_minor"])
                if payload.get("accrued_interest_minor") is not None
                else None
            ),
            "escrow_balance_minor": abs(payload.get("escrow_balance_minor", 0)),
            "unapplied_credit_minor": (
                abs(payload["unapplied_credit_minor"])
                if payload.get("unapplied_credit_minor") is not None
                else None
            ),
            "ytd_principal_paid_minor": (
                abs(payload["ytd_principal_paid_minor"])
                if payload.get("ytd_principal_paid_minor") is not None
                else None
            ),
            "ytd_interest_paid_minor": (
                abs(payload["ytd_interest_paid_minor"])
                if payload.get("ytd_interest_paid_minor") is not None
                else None
            ),
            "attributed_payment_minor": attributed_payment,
            "principal_reduction_minor": principal_reduction,
            "unknown_nonprincipal_minor": unknown_nonprincipal,
            "notes": payload.get("notes", ""),
            "created_at": existing["created_at"] if existing else now,
            "created_by_user_id": None,
        }
        with self.db.transaction() as connection:
            if existing:
                replace_current_version(
                    connection,
                    "loan_balance_snapshots",
                    "snapshot_id",
                    snapshot_id,
                    {"row_id": str(uuid4())} | values,
                    now=now,
                )
            else:
                insert_version(
                    connection,
                    "loan_balance_snapshots",
                    values | {"valid_from": now, "valid_to": MAX_TS},
                )
        return {"snapshot_id": snapshot_id}

    def list_loan_snapshots(self, account_id: str) -> list[dict[str, Any]]:
        return self.db.fetch_all(
            load_sql("queries/current_loan_balance_snapshots_by_account"),
            (account_id,),
        )

    def get_loan_projection(self, account_id: str) -> dict[str, object]:
        self._require_account_class(account_id, ACCOUNT_CLASS_LOAN)
        details = self.db.fetch_one(
            load_sql("queries/current_loan_details_by_account"), (account_id,)
        )
        snapshots = self.list_loan_snapshots(account_id)
        if details is None or not snapshots:
            return {"available": False, "missing": ["current principal statement"], "rows": []}
        latest = snapshots[0]
        return project_loan(
            LoanProjectionTerms(
                principal_minor=int(latest["principal_balance_minor"]),
                principal_as_of=latest["effective_date"],
                annual_rate_minor=(
                    int(details["rate_minor"]) if details.get("rate_minor") is not None else None
                ),
                rate_type=details.get("rate_type"),
                scheduled_payment_minor=(
                    int(details["scheduled_principal_interest_minor"])
                    if details.get("scheduled_principal_interest_minor") is not None
                    else None
                ),
                payment_frequency=cast(PaymentFrequency | None, details.get("payment_frequency")),
                next_payment_date=details.get("next_payment_date"),
                maturity_date=details.get("maturity_date"),
                remaining_term_months=(
                    int(details["remaining_term_months"])
                    if details.get("remaining_term_months") is not None
                    else None
                ),
                recurring_extra_principal_minor=int(
                    details.get("recurring_extra_principal_minor") or 0
                ),
            ),
            as_of=self.clock.today(),
        )

    def create_loan_payment(self, loan_account_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        self._require_account_class(loan_account_id, ACCOUNT_CLASS_LOAN)
        self._require_account_class(payload["budget_account_id"], ACCOUNT_CLASS_BUDGET)
        payment_date = payload["date"]
        if isinstance(payment_date, str):
            payment_date = date.fromisoformat(payment_date)
        link = self._effective_account_budget_link(
            loan_account_id,
            LINK_BEHAVIOR_LOAN_PAYMENT,
            payment_date,
        )
        if link is None:
            raise ValueError("Configure a loan payment category before recording a payment")
        return self.create_transaction(
            {
                "date": payment_date,
                "account_id": payload["budget_account_id"],
                "amount_minor": -abs(payload["amount_minor"]),
                "category_id": str(link["category_id"]),
                "system_category": None,
                "status": payload["status"],
                "memo": payload.get("memo", "Loan payment"),
                "loan_account_id": loan_account_id,
            }
        )

    def list_loan_payments(self, loan_account_id: str) -> list[dict[str, Any]]:
        self._require_account_class(loan_account_id, ACCOUNT_CLASS_LOAN)
        return self.db.fetch_all(
            load_sql("queries/loan_attributed_transactions"),
            (loan_account_id,),
        )

    def create_tangible_asset_valuation(
        self, account_id: str, payload: dict[str, Any]
    ) -> dict[str, Any]:
        self._require_account_class(account_id, ACCOUNT_CLASS_TANGIBLE_ASSET)
        effective_date = self._non_future_date(payload["effective_date"])
        now = self.clock.now()
        existing = self.db.fetch_one(
            load_sql("queries/current_tangible_valuation_by_account_date"),
            (account_id, effective_date),
        )
        valuation_id = str(existing["valuation_id"]) if existing else str(uuid4())
        values = {
            "valuation_id": valuation_id,
            "account_id": account_id,
            "effective_date": effective_date,
            "amount_minor": abs(payload["amount_minor"]),
            "source": payload.get("source", "manual"),
            "notes": payload.get("notes", ""),
            "created_at": existing["created_at"] if existing else now,
            "created_by_user_id": existing["created_by_user_id"] if existing else None,
        }
        with self.db.transaction() as connection:
            if existing:
                replace_current_version(
                    connection,
                    "tangible_asset_valuations",
                    "valuation_id",
                    valuation_id,
                    {"row_id": str(uuid4())} | values,
                    now=now,
                )
            else:
                insert_version(
                    connection,
                    "tangible_asset_valuations",
                    values | {"valid_from": now, "valid_to": MAX_TS},
                )
        return {"valuation_id": valuation_id}

    def list_tangible_asset_valuations(self, account_id: str) -> list[dict[str, Any]]:
        return self.db.fetch_all(
            load_sql("queries/current_tangible_asset_valuations_by_account"),
            (account_id,),
        )

    def create_category_group(self, payload: dict[str, Any]) -> dict[str, Any]:
        now = self.clock.now()
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
            load_sql("queries/current_category_group_by_id"),
            (group_id,),
        )
        if current is None:
            raise ValueError("Category group not found")
        now = self.clock.now()
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
        now = self.clock.now()
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
                    "goal_type": payload.get("goal_type"),
                    "goal_amount_minor": payload.get("goal_amount_minor"),
                    "goal_frequency": payload.get("goal_frequency"),
                    "goal_due_date": payload.get("goal_due_date"),
                    "metadata": json_dumps(
                        {"icon": payload.get("icon")} if payload.get("icon") else {}
                    ),
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
            load_sql("queries/current_category_by_id"),
            (category_id,),
        )
        if current is None:
            raise ValueError("Category not found")
        now = self.clock.now()
        current_metadata = cast(
            dict[str, Any],
            self._decode_json_fields(current, {"metadata"}).get("metadata") or {},
        )
        if "icon" in payload:
            icon = payload.get("icon")
            if icon:
                current_metadata["icon"] = icon
            else:
                current_metadata.pop("icon", None)
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
                    "goal_type": payload.get("goal_type", current["goal_type"]),
                    "goal_amount_minor": payload.get(
                        "goal_amount_minor", current["goal_amount_minor"]
                    ),
                    "goal_frequency": payload.get("goal_frequency", current["goal_frequency"]),
                    "goal_due_date": payload.get("goal_due_date", current["goal_due_date"]),
                    "metadata": json_dumps(current_metadata),
                    "created_at": current["created_at"],
                    "created_by_user_id": current["created_by_user_id"],
                },
                now=now,
            )
        return {"category_id": category_id}

    def get_category_goal(self, category_id: str) -> dict[str, Any]:
        current = self.db.fetch_one(
            load_sql("queries/current_category_by_id"),
            (category_id,),
        )
        if current is None:
            raise ValueError("Category not found")
        monthly_funding = self._compute_monthly_funding(current)
        return {
            "category_id": category_id,
            "goal_type": current["goal_type"],
            "goal_amount_minor": current["goal_amount_minor"],
            "goal_frequency": current["goal_frequency"],
            "goal_due_date": str(current["goal_due_date"]) if current["goal_due_date"] else None,
            "monthly_funding_minor": monthly_funding,
        }

    def update_category_goal(self, category_id: str, payload: dict[str, Any]) -> dict[str, Any]:
        current = self.db.fetch_one(
            load_sql("queries/current_category_by_id"),
            (category_id,),
        )
        if current is None:
            raise ValueError("Category not found")
        now = self.clock.now()
        with self.db.transaction() as connection:
            replace_current_version(
                connection,
                "categories",
                "category_id",
                category_id,
                {
                    "row_id": str(uuid4()),
                    "category_id": category_id,
                    "group_id": current["group_id"],
                    "name": current["name"],
                    "category_kind": current["category_kind"],
                    "sort_order": current["sort_order"],
                    "is_hidden": current["is_hidden"],
                    "is_active": current["is_active"],
                    "target_amount_minor": current["target_amount_minor"],
                    "due_date_rule": current["due_date_rule"],
                    "goal_type": payload.get("goal_type", current["goal_type"]),
                    "goal_amount_minor": payload.get(
                        "goal_amount_minor", current["goal_amount_minor"]
                    ),
                    "goal_frequency": payload.get("goal_frequency", current["goal_frequency"]),
                    "goal_due_date": payload.get("goal_due_date", current["goal_due_date"]),
                    "metadata": current["metadata"],
                    "created_at": current["created_at"],
                    "created_by_user_id": current["created_by_user_id"],
                },
                now=now,
            )
        return {"category_id": category_id}

    def _compute_monthly_funding(self, category: dict[str, Any]) -> int:
        goal_type = category.get("goal_type")
        goal_amount = category.get("goal_amount_minor")
        if goal_type is None or goal_amount is None:
            return 0
        goal_amount = int(goal_amount)

        if goal_type == "ONE_TIME":
            goal_due_date = category.get("goal_due_date")
            if goal_due_date is None:
                return 0
            today = self.clock.now().date()
            if isinstance(goal_due_date, str):
                goal_due_date = date.fromisoformat(goal_due_date)
            months_remaining = max(
                1,
                (goal_due_date.year - today.year) * 12 + (goal_due_date.month - today.month),
            )
            return goal_amount // months_remaining

        if goal_type == "RECURRING":
            frequency = category.get("goal_frequency", "MONTHLY")
            if frequency == "WEEKLY":
                return (goal_amount * 52) // 12
            if frequency == "EVERY_2_WEEKS":
                return (goal_amount * 26) // 12
            if frequency == "TWICE_MONTHLY":
                return goal_amount * 2
            if frequency == "EVERY_2_MONTHS":
                return goal_amount // 2
            if frequency == "QUARTERLY":
                return goal_amount // 3
            if frequency == "EVERY_6_MONTHS":
                return goal_amount // 6
            if frequency == "YEARLY":
                return goal_amount // 12
            return goal_amount

        if goal_type == "DISCRETIONARY":
            return goal_amount

        return 0

    def compute_available_to_budget(self) -> int:
        transactions = self.db.fetch_all(
            load_sql("queries/available_to_budget_transactions"),
            (
                ACCOUNT_CLASS_BUDGET,
                SYSTEM_CATEGORY_ATB,
                SYSTEM_CATEGORY_STARTING_BALANCE,
                SYSTEM_CATEGORY_BALANCE_ADJUSTMENT,
            ),
        )
        allocations = self.db.fetch_all(load_sql("queries/current_allocations_amount_only"))
        transfer_facts = [
            TransferBoundaryFact(
                transaction_id=str(row["transaction_id"]),
                account_class=str(row["account_class"]),
                system_category=row["system_category"],
                amount_minor=int(row["amount_minor"]),
                effective_date=row["effective_date"],
                status=str(row["status"]),
            )
            for row in self.db.fetch_all(load_sql("queries/current_transfer_boundary_facts"))
        ]
        total = compute_transfer_boundary_adjustment(transfer_facts, as_of=self.clock.today())
        for transaction in transactions:
            if transaction["system_category"] == SYSTEM_CATEGORY_TRANSFER:
                continue
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
        category = next(
            (
                item
                for item in self.list_categories(
                    month=self.default_budget_month(), show_hidden=True
                )
                if item["category_id"] == category_id
            ),
            None,
        )
        if category is None:
            raise ValueError("Category not found")
        return int(category["available_minor"])

    def compute_month_activity(self, category_id: str, month_start: date, month_end: date) -> int:
        transactions = self.db.fetch_all(
            load_sql("queries/current_transactions_by_category_amount_date"),
            (category_id,),
        )
        return sum(
            transaction["amount_minor"]
            for transaction in transactions
            if month_start <= transaction["date"] <= month_end
        )

    def compute_month_budgeted(self, bucket_id: str, month_start: date, month_end: date) -> int:
        allocations = self.db.fetch_all(load_sql("queries/current_allocations_amount_date"))
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
            load_sql("queries/current_transactions_by_category_amount_date"),
            (category_id,),
        )
        allocations = self.db.fetch_all(load_sql("queries/current_allocations_amount_date"))
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
            load_sql("queries/current_transactions_by_system_category_amount_date"),
            (SYSTEM_CATEGORY_ATB,),
        )
        return sum(
            transaction["amount_minor"]
            for transaction in transactions
            if transaction["amount_minor"] > 0 and month_start <= transaction["date"] <= month_end
        )

    def compute_spent(self, month_start: date, month_end: date, *, show_hidden: bool) -> int:
        categories = {
            row["category_id"]: row
            for row in self.db.fetch_all(load_sql("queries/current_categories"))
        }
        transactions = self.db.fetch_all(
            load_sql("queries/current_transactions_amount_date_category")
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

    def _account_balances(self, through_date: date | None = None) -> dict[str, dict[str, int]]:
        if through_date is None:
            rows = self.db.fetch_all(load_sql("queries/account_balances"))
        else:
            rows = self.db.fetch_all(
                load_sql("queries/account_balances_through_date"), (through_date,)
            )
        return {
            row["account_id"]: {
                "actual": row["actual"],
                "pending": row["pending"],
                "cleared": row["cleared"],
            }
            for row in rows
        }

    def _account_values(
        self,
        accounts: list[dict[str, Any]],
        balances: dict[str, dict[str, int]],
        previous_balances: dict[str, dict[str, int]],
        as_of: date,
    ) -> dict[str, AccountValue]:
        previous_date = as_of - timedelta(days=30)
        tracking = self._rows_by_account("queries/latest_tracking_valuations_through_date", as_of)
        previous_tracking = self._rows_by_account(
            "queries/latest_tracking_valuations_through_date", previous_date
        )
        tangible = self._rows_by_account("queries/latest_tangible_valuations_through_date", as_of)
        previous_tangible = self._rows_by_account(
            "queries/latest_tangible_valuations_through_date", previous_date
        )
        loans = self._rows_by_account("queries/latest_loan_balances_through_date", as_of)
        previous_loans = self._rows_by_account(
            "queries/latest_loan_balances_through_date", previous_date
        )
        investment_values = self._investment_values(accounts, as_of)
        previous_investment_values = self._investment_values(accounts, previous_date)

        values: dict[str, AccountValue] = {}
        for account in accounts:
            account_id = str(account["account_id"])
            account_class = account["account_class"]
            if account_class == ACCOUNT_CLASS_BUDGET:
                current = balances.get(account_id, {"actual": 0})["actual"]
                previous = previous_balances.get(account_id, {"actual": 0})["actual"]
                values[account_id] = ledger_value(current, previous)
            elif account_class == ACCOUNT_CLASS_TRACKING:
                row = tracking.get(account_id)
                previous_row = previous_tracking.get(account_id)
                factory = (
                    liability_value
                    if account.get("tracking_polarity") == "LIABILITY"
                    else asset_value
                )
                values[account_id] = factory(
                    row["amount_minor"] if row else None,
                    source_of_truth=(
                        "imported_valuation"
                        if account.get("tracking_source") == "import"
                        else "snapshot"
                    ),
                    effective_date=row["effective_date"] if row else None,
                    previous_amount_minor=(previous_row["amount_minor"] if previous_row else None),
                )
            elif account_class == ACCOUNT_CLASS_TANGIBLE_ASSET:
                row = tangible.get(account_id)
                previous_row = previous_tangible.get(account_id)
                values[account_id] = asset_value(
                    row["amount_minor"] if row else None,
                    source_of_truth="manual_valuation",
                    effective_date=row["effective_date"] if row else None,
                    previous_amount_minor=(previous_row["amount_minor"] if previous_row else None),
                )
            elif account_class == ACCOUNT_CLASS_LOAN:
                row = loans.get(account_id)
                previous_row = previous_loans.get(account_id)
                loan_current: int | None = (
                    int(row["principal_balance_minor"])
                    + int(row.get("accrued_interest_minor") or 0)
                    if row
                    else None
                )
                loan_previous: int | None = (
                    int(previous_row["principal_balance_minor"])
                    + int(previous_row.get("accrued_interest_minor") or 0)
                    if previous_row
                    else None
                )
                if row is None:
                    values[account_id] = unavailable_value("loan_statement")
                else:
                    escrow = int(row.get("escrow_balance_minor") or 0)
                    unapplied = int(row.get("unapplied_credit_minor") or 0)
                    net_worth = -(loan_current or 0) + escrow + unapplied
                    previous_net_worth = None
                    if previous_row is not None:
                        previous_net_worth = (
                            -(loan_previous or 0)
                            + int(previous_row.get("escrow_balance_minor") or 0)
                            + int(previous_row.get("unapplied_credit_minor") or 0)
                        )
                    values[account_id] = AccountValue(
                        current_value_minor=loan_current,
                        net_worth_minor=net_worth,
                        source_of_truth="loan_statement",
                        effective_date=row["effective_date"],
                        change_minor=(
                            net_worth - previous_net_worth
                            if previous_net_worth is not None
                            else None
                        ),
                        reconciliation_status="CURRENT",
                        liability_minor=-(loan_current or 0),
                        restricted_asset_minor=escrow,
                        unapplied_credit_minor=unapplied,
                    )
            elif account_class == ACCOUNT_CLASS_INVESTMENT:
                current_input = investment_values.get(account_id)
                previous_input = previous_investment_values.get(account_id)
                if current_input is None:
                    values[account_id] = unavailable_value("investment_statement")
                else:
                    current_amount, effective_date, provisional = current_input
                    previous_amount = previous_input[0] if previous_input else None
                    values[account_id] = AccountValue(
                        current_value_minor=current_amount,
                        net_worth_minor=current_amount,
                        source_of_truth="investment_statement",
                        effective_date=effective_date,
                        change_minor=(
                            current_amount - previous_amount
                            if previous_amount is not None
                            else None
                        ),
                        reconciliation_status=("PROVISIONAL" if provisional != 0 else "CURRENT"),
                        provisional_minor=provisional,
                    )
            else:
                values[account_id] = unavailable_value("unknown")
        return values

    def _rows_by_account(self, query_name: str, through_date: date) -> dict[str, dict[str, Any]]:
        return {
            str(row["account_id"]): row
            for row in self.db.fetch_all(load_sql(query_name), (through_date,))
        }

    def _require_account_class(self, account_id: str, expected_class: str) -> None:
        account = self._require_account(account_id)
        if account["account_class"] != expected_class:
            raise ValueError(f"Account must be {expected_class}")

    def _non_future_date(self, value: date | str, *, field_name: str = "Effective date") -> date:
        parsed = date.fromisoformat(value) if isinstance(value, str) else value
        if parsed > self.clock.today():
            raise ValueError(f"{field_name} cannot be in the future")
        return parsed

    def _next_financial_event_order(self, connection: Any) -> int:
        row = connection.execute(load_sql("queries/next_financial_event_order")).fetchone()
        assert row is not None
        return int(row[0])

    def _effective_account_budget_link(
        self, account_id: str, behavior: str, effective_date: date
    ) -> dict[str, Any] | None:
        return next(
            (
                link
                for link in self.db.fetch_all(
                    load_sql("queries/account_budget_link_effective_intervals")
                )
                if str(link["account_id"]) == account_id
                and link["link_behavior"] == behavior
                and link["effective_date"] <= effective_date
                and (link.get("end_date") is None or effective_date < link["end_date"])
            ),
            None,
        )

    def _require_account(self, account_id: str) -> dict[str, Any]:
        account = self.db.fetch_one(load_sql("queries/current_account_by_id"), (account_id,))
        if account is None:
            raise ValueError("Account not found")
        return account

    def _require_distinct_accounts(self, from_account_id: str, to_account_id: str) -> None:
        self._require_account(from_account_id)
        self._require_account(to_account_id)
        if from_account_id == to_account_id:
            raise ValueError("Transfer accounts must be different")

    def _create_rich_account_operation(
        self, *, endpoint_account_id: str, payload: dict[str, Any], operation_kind: str
    ) -> dict[str, Any]:
        if int(payload["amount_minor"]) <= 0:
            raise ValueError("Operation amount must be positive")
        source_id = str(payload["source_account_id"])
        destination_id = str(payload["destination_account_id"])
        source = self._require_account(source_id)
        destination = self._require_account(destination_id)
        if not source["is_active"] or not destination["is_active"]:
            raise ValueError("Operation accounts must be active")
        if endpoint_account_id not in {source_id, destination_id}:
            raise ValueError("Operation endpoint account does not match its leg")
        if operation_kind == "INVESTMENT_CONTRIBUTION":
            self._require_deposit_account(source_id)
            if destination["account_class"] != ACCOUNT_CLASS_INVESTMENT:
                raise ValueError("Contribution destination must be an investment account")
        elif operation_kind == "INVESTMENT_WITHDRAWAL":
            if source["account_class"] != ACCOUNT_CLASS_INVESTMENT:
                raise ValueError("Withdrawal source must be an investment account")
            self._require_deposit_account(destination_id)
            current_value = self._investment_values(
                self.db.fetch_all(load_sql("queries/list_accounts")), self.clock.today()
            ).get(source_id)
            if current_value is None or current_value[0] < int(payload["amount_minor"]):
                raise ValueError("Withdrawal exceeds the current investment value")
        elif operation_kind == "CREDIT_CARD_PAYMENT":
            self._require_deposit_account(source_id)
            settings = self.db.fetch_one(
                load_sql("queries/current_budget_account_settings_by_account"), (destination_id,)
            )
            if (
                destination_id != endpoint_account_id
                or settings is None
                or settings["budget_account_type"] != BUDGET_ACCOUNT_TYPE_CREDIT_CARD
            ):
                raise ValueError("Payment destination must be the credit-card account")
        else:
            raise ValueError("Unsupported rich operation")

        source_date = payload["source_posted_date"]
        destination_date = payload["destination_posted_date"]
        if isinstance(source_date, str):
            source_date = date.fromisoformat(source_date)
        if isinstance(destination_date, str):
            destination_date = date.fromisoformat(destination_date)
        request = payload | {
            "endpoint_account_id": endpoint_account_id,
            "operation_kind": operation_kind,
        }
        now = self.clock.now()

        def apply(connection: Any, fingerprint: str) -> dict[str, Any]:
            linked_category_id = None
            if operation_kind == "INVESTMENT_CONTRIBUTION":
                link = self._effective_account_budget_link(
                    destination_id, LINK_BEHAVIOR_INVESTMENT_CONTRIBUTION, destination_date
                )
                if link is None:
                    raise ValueError(
                        "Configure an investment contribution category before contributing"
                    )
                linked_category_id = str(link["category_id"])
            operation_id = str(uuid4())
            result = self._insert_transfer(
                connection,
                from_account_id=source_id,
                to_account_id=destination_id,
                amount_minor=payload["amount_minor"],
                source_date=source_date,
                destination_date=destination_date,
                source_status=payload["source_status"],
                destination_status=payload["destination_status"],
                memo=payload.get("memo", ""),
                now=now,
            )
            create_transaction_operation(
                connection,
                operation_id=operation_id,
                operation_kind=operation_kind,
                origin="ACCOUNT_DETAIL",
                client_operation_id=payload["client_operation_id"],
                request_fingerprint=fingerprint,
                created_at=now,
            )
            link_transaction_operation(
                connection,
                operation_id=operation_id,
                transaction_id=result["source_transaction_id"],
                leg_role="SOURCE",
                now=now,
            )
            link_transaction_operation(
                connection,
                operation_id=operation_id,
                transaction_id=result["destination_transaction_id"],
                leg_role="DESTINATION",
                now=now,
            )
            return result | {
                "operation_id": operation_id,
                "operation_kind": operation_kind,
                "linked_category_id": linked_category_id,
            }

        return execute_financial_command(
            self.db,
            client_operation_id=payload["client_operation_id"],
            command_kind=operation_kind,
            request=request,
            command=apply,
            now=now,
        )

    def _require_deposit_account(self, account_id: str) -> None:
        account = self._require_account(account_id)
        settings = self.db.fetch_one(
            load_sql("queries/current_budget_account_settings_by_account"), (account_id,)
        )
        if (
            account["account_class"] != ACCOUNT_CLASS_BUDGET
            or not account["is_active"]
            or settings is None
            or settings["budget_account_type"] != BUDGET_ACCOUNT_TYPE_DEPOSIT
        ):
            raise ValueError("Operation requires a budget deposit account")

    def _insert_transfer(
        self,
        connection: Any,
        *,
        from_account_id: str,
        to_account_id: str,
        amount_minor: int,
        transfer_date: date | None = None,
        source_date: date | None = None,
        destination_date: date | None = None,
        memo: str,
        status: str | None = None,
        source_status: str | None = None,
        destination_status: str | None = None,
        now: datetime,
    ) -> dict[str, Any]:
        self._require_distinct_accounts(from_account_id, to_account_id)
        source_transaction_id = str(uuid4())
        destination_transaction_id = str(uuid4())
        max_row = connection.execute(load_sql("queries/max_entry_order")).fetchone()
        next_order = int(max_row[0]) + 1 if max_row else 1
        record_order = self._next_financial_event_order(connection)
        for index, (transaction_id, account_id, signed_amount) in enumerate(
            (
                (source_transaction_id, from_account_id, -amount_minor),
                (destination_transaction_id, to_account_id, amount_minor),
            )
        ):
            insert_version(
                connection,
                "transactions",
                {
                    "transaction_id": transaction_id,
                    "date": (
                        source_date
                        if index == 0 and source_date is not None
                        else destination_date
                        if index == 1 and destination_date is not None
                        else transfer_date
                    ),
                    "account_id": account_id,
                    "amount_minor": signed_amount,
                    "category_id": None,
                    "system_category": SYSTEM_CATEGORY_TRANSFER,
                    "status": (
                        source_status
                        if index == 0 and source_status is not None
                        else destination_status
                        if index == 1 and destination_status is not None
                        else status
                    ),
                    "memo": memo,
                    "entry_order": next_order,
                    "record_order": record_order,
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
            next_order += 1
        return {
            "source_transaction_id": source_transaction_id,
            "destination_transaction_id": destination_transaction_id,
        }

    def _insert_loan_attribution_if_applicable(
        self,
        connection: Any,
        *,
        transaction_id: str,
        category_id: str | None,
        transaction_date: date,
        explicit_loan_account_id: str | None,
        now: datetime,
    ) -> None:
        if isinstance(transaction_date, str):
            transaction_date = date.fromisoformat(transaction_date)
        existing = self.db.fetch_one(
            load_sql("queries/current_loan_attribution_by_transaction"),
            (transaction_id,),
        )
        if existing:
            close_current_version(
                connection,
                "loan_transaction_attributions",
                "attribution_id",
                str(existing["attribution_id"]),
                now=now,
            )
        if category_id is None:
            return
        candidates = [
            link
            for link in self.db.fetch_all(
                load_sql("queries/current_account_budget_links_by_category"),
                (category_id,),
            )
            if link["link_behavior"] == LINK_BEHAVIOR_LOAN_PAYMENT
            and link["effective_date"] <= transaction_date
        ]
        if explicit_loan_account_id:
            loan_account_id = explicit_loan_account_id
            if loan_account_id not in {str(link["account_id"]) for link in candidates}:
                raise ValueError("Loan is not linked to the selected payment category")
        elif len(candidates) == 1:
            loan_account_id = str(candidates[0]["account_id"])
        else:
            return
        insert_version(
            connection,
            "loan_transaction_attributions",
            {
                "attribution_id": (str(existing["attribution_id"]) if existing else str(uuid4())),
                "transaction_id": transaction_id,
                "loan_account_id": loan_account_id,
                "valid_from": now,
                "valid_to": MAX_TS,
                "created_at": existing["created_at"] if existing else now,
                "created_by_user_id": None,
            },
        )

    def _investment_values(
        self, accounts: list[dict[str, Any]], as_of: date
    ) -> dict[str, tuple[int, date, int]]:
        cash_by_account = self._rows_by_account(
            "queries/latest_investment_cash_through_date", as_of
        )
        values: dict[str, tuple[int, date, int]] = {}
        for account in accounts:
            if account["account_class"] != ACCOUNT_CLASS_INVESTMENT:
                continue
            account_id = str(account["account_id"])
            cash = cash_by_account.get(account_id)
            if cash is None:
                continue
            statement_date = cash["effective_date"]
            positions = self.db.fetch_all(
                load_sql("queries/current_investment_positions_by_account_date"),
                (account_id, statement_date),
            )
            holdings_value = 0
            complete = True
            for position in positions:
                price = self.db.fetch_one(
                    load_sql("queries/current_investment_price_by_ticker_date"),
                    (account_id, position["ticker"], statement_date, account_id),
                )
                if price is None:
                    complete = False
                    break
                holdings_value += position_amount_minor(
                    int(position["quantity_micros"]), int(price["price_minor"])
                )
            if not complete:
                continue
            transfer_row = self.db.fetch_one(
                load_sql("queries/investment_transfer_delta_after_date"),
                (account_id, statement_date, statement_date, cash["record_order"], as_of),
            )
            provisional = int(transfer_row["transfer_delta_minor"] if transfer_row else 0)
            amount = int(cash["cash_balance_minor"]) + holdings_value + provisional
            values[account_id] = (amount, statement_date, provisional)
        return values

    def _replace_statement_price(
        self,
        connection: Any,
        *,
        account_id: str,
        ticker: str,
        effective_date: date,
        price_minor: int,
        now: datetime,
    ) -> None:
        existing = self.db.fetch_one(
            load_sql("queries/current_investment_price_by_ticker_date"),
            (account_id, ticker, effective_date, account_id),
        )
        snapshot_id = str(existing["snapshot_id"]) if existing else str(uuid4())
        if existing and existing.get("account_id") == account_id:
            close_current_version(
                connection,
                "investment_price_snapshots",
                "snapshot_id",
                snapshot_id,
                now=now,
            )
        else:
            snapshot_id = str(uuid4())
        insert_version(
            connection,
            "investment_price_snapshots",
            {
                "snapshot_id": snapshot_id,
                "account_id": account_id,
                "ticker": ticker,
                "effective_date": effective_date,
                "price_minor": price_minor,
                "source": "statement",
                "valid_from": now,
                "valid_to": MAX_TS,
                "created_at": (
                    existing["created_at"]
                    if existing and existing.get("account_id") == account_id
                    else now
                ),
                "created_by_user_id": None,
            },
        )

    def _validate_transaction_payload(
        self, payload: dict[str, Any], *, new_entry: bool = False
    ) -> None:
        has_category = payload.get("category_id") is not None
        has_system = payload.get("system_category") is not None
        if has_category == has_system:
            raise ValueError("Exactly one of category_id or system_category must be set")
        if not new_entry:
            return

        account = self._require_account(str(payload["account_id"]))
        if not account["is_active"]:
            raise ValueError("Account is not active")
        account_class = account["account_class"]
        system_category = payload.get("system_category")
        if system_category == SYSTEM_CATEGORY_TRANSFER:
            if account_class not in {ACCOUNT_CLASS_BUDGET, ACCOUNT_CLASS_INVESTMENT}:
                raise ValueError("Account transfers require a budget or investment account")
            return
        if account_class != ACCOUNT_CLASS_BUDGET:
            raise ValueError("Only budget accounts can use categories or Available to budget")
        if system_category == SYSTEM_CATEGORY_ATB:
            return
        if system_category is not None:
            raise ValueError("This system category is not available for new entries")

        category = self.db.fetch_one(
            load_sql("queries/current_category_by_id"), (payload["category_id"],)
        )
        if category is None or not category["is_active"]:
            raise ValueError("Category is not active")
        if category["category_kind"] != CATEGORY_KIND_STANDARD:
            raise ValueError("New entries require a standard category")

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

    def _cutover_successor_value(self, successor: dict[str, Any]) -> int:
        if successor["account_class"] == ACCOUNT_CLASS_INVESTMENT:
            holdings_value = sum(
                position_amount_minor(int(holding["quantity_micros"]), int(holding["price_minor"]))
                for holding in successor["holdings"]
            )
            return int(successor["cash_balance_minor"]) + holdings_value
        if successor["account_class"] == ACCOUNT_CLASS_LOAN:
            obligation = int(successor["principal_balance_minor"]) + int(
                successor.get("accrued_interest_minor") or 0
            )
            return (
                -obligation
                + int(successor.get("escrow_balance_minor") or 0)
                + int(successor.get("unapplied_credit_minor") or 0)
            )
        return int(successor["opening_value_minor"])

    def _insert_cutover_successor(
        self,
        connection: Any,
        *,
        operation_id: str,
        successor_order: int,
        successor_id: str,
        successor: dict[str, Any],
        cutover_date: date,
        opening_net_worth_minor: int,
        now: datetime,
    ) -> None:
        account_class = successor["account_class"]
        insert_version(
            connection,
            "accounts",
            {
                "account_id": successor_id,
                "account_class": account_class,
                "name": successor["name"],
                "institution": successor.get("institution"),
                "account_number_last4": successor.get("account_number_last4"),
                "is_hidden": False,
                "is_active": True,
                "metadata": json_dumps(
                    {"cutover_operation_id": operation_id, "successor_order": successor_order}
                ),
                "valid_from": now,
                "valid_to": MAX_TS,
                "created_at": now,
                "created_by_user_id": None,
            },
        )
        if account_class == ACCOUNT_CLASS_INVESTMENT:
            insert_version(
                connection,
                "investment_account_details",
                {
                    "account_id": successor_id,
                    "self_managed": successor.get("self_managed", False),
                    "tax_treatment": successor.get("tax_treatment", "TAXABLE_BROKERAGE"),
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
            for holding_index, holding in enumerate(successor["holdings"]):
                ticker = holding["ticker"].strip().upper()
                insert_version(
                    connection,
                    "investment_positions",
                    {
                        "position_id": str(
                            uuid5(
                                NAMESPACE_URL,
                                f"dojo:cutover:{operation_id}:{successor_order}:position:{holding_index}",
                            )
                        ),
                        "account_id": successor_id,
                        "ticker": ticker,
                        "effective_date": cutover_date,
                        "quantity_micros": holding["quantity_micros"],
                        "average_basis_minor": holding["average_basis_minor"],
                        "valid_from": now,
                        "valid_to": MAX_TS,
                        "created_at": now,
                        "created_by_user_id": None,
                    },
                )
                insert_version(
                    connection,
                    "investment_price_snapshots",
                    {
                        "snapshot_id": str(
                            uuid5(
                                NAMESPACE_URL,
                                f"dojo:cutover:{operation_id}:{successor_order}:price:{holding_index}",
                            )
                        ),
                        "account_id": successor_id,
                        "ticker": ticker,
                        "effective_date": cutover_date,
                        "price_minor": holding["price_minor"],
                        "source": "cutover",
                        "valid_from": now,
                        "valid_to": MAX_TS,
                        "created_at": now,
                        "created_by_user_id": None,
                    },
                )
            record_order = self._next_financial_event_order(connection)
            insert_version(
                connection,
                "investment_cash_snapshots",
                {
                    "snapshot_id": str(
                        uuid5(
                            NAMESPACE_URL,
                            f"dojo:cutover:{operation_id}:{successor_order}:cash",
                        )
                    ),
                    "account_id": successor_id,
                    "effective_date": cutover_date,
                    "cash_balance_minor": successor["cash_balance_minor"],
                    "record_order": record_order,
                    "notes": "Opening value from tracking cutover",
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
            if successor.get("contribution_category_id"):
                self._create_account_budget_link(
                    connection,
                    successor_id,
                    successor["contribution_category_id"],
                    LINK_BEHAVIOR_INVESTMENT_CONTRIBUTION,
                    DERIVATION_METHOD_TRANSFER_IN_ONLY,
                    now,
                    effective_date=cutover_date,
                )
        elif account_class == ACCOUNT_CLASS_LOAN:
            insert_version(
                connection,
                "loan_details",
                {
                    "account_id": successor_id,
                    "original_amount_minor": successor.get("original_amount_minor"),
                    "origination_date": successor.get("origination_date"),
                    "rate_minor": successor.get("rate_minor"),
                    "rate_type": successor.get("rate_type"),
                    "scheduled_principal_interest_minor": successor.get(
                        "scheduled_principal_interest_minor"
                    ),
                    "payment_frequency": successor.get("payment_frequency"),
                    "next_payment_date": successor.get("next_payment_date"),
                    "maturity_date": successor.get("maturity_date"),
                    "remaining_term_months": successor.get("remaining_term_months"),
                    "recurring_extra_principal_minor": successor.get(
                        "recurring_extra_principal_minor"
                    ),
                    "status": "IN_REPAYMENT",
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
            insert_version(
                connection,
                "loan_balance_snapshots",
                {
                    "snapshot_id": str(
                        uuid5(
                            NAMESPACE_URL,
                            f"dojo:cutover:{operation_id}:{successor_order}:loan-balance",
                        )
                    ),
                    "account_id": successor_id,
                    "effective_date": cutover_date,
                    "principal_balance_minor": successor["principal_balance_minor"],
                    "accrued_interest_minor": successor.get("accrued_interest_minor"),
                    "escrow_balance_minor": successor.get("escrow_balance_minor", 0),
                    "unapplied_credit_minor": successor.get("unapplied_credit_minor"),
                    "ytd_principal_paid_minor": None,
                    "ytd_interest_paid_minor": None,
                    "attributed_payment_minor": 0,
                    "principal_reduction_minor": 0,
                    "unknown_nonprincipal_minor": 0,
                    "notes": "Opening balance from tracking cutover",
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
            self._create_account_budget_link(
                connection,
                successor_id,
                successor["payment_category_id"],
                LINK_BEHAVIOR_LOAN_PAYMENT,
                DERIVATION_METHOD_TRANSFER_IN_ONLY,
                now,
                effective_date=cutover_date,
            )
        else:
            insert_version(
                connection,
                "tangible_asset_valuations",
                {
                    "valuation_id": str(
                        uuid5(
                            NAMESPACE_URL,
                            f"dojo:cutover:{operation_id}:{successor_order}:valuation",
                        )
                    ),
                    "account_id": successor_id,
                    "effective_date": cutover_date,
                    "amount_minor": successor["opening_value_minor"],
                    "source": "cutover",
                    "notes": "Opening value from tracking cutover",
                    "valid_from": now,
                    "valid_to": MAX_TS,
                    "created_at": now,
                    "created_by_user_id": None,
                },
            )
        connection.execute(
            load_sql("queries/insert_tracking_cutover_successor"),
            (operation_id, successor_order, successor_id, opening_net_worth_minor),
        )

    def _tracking_cutover_response(self, cutover: dict[str, Any]) -> dict[str, Any]:
        successors = self.db.fetch_all(
            load_sql("queries/tracking_cutover_successors_by_operation"),
            (cutover["operation_id"],),
        )
        return {
            "operation_id": str(cutover["operation_id"]),
            "predecessor_account_id": str(cutover["predecessor_account_id"]),
            "cutover_date": str(cutover["cutover_date"]),
            "prior_value_minor": int(cutover["prior_value_minor"]),
            "successor_total_minor": int(cutover["successor_total_minor"]),
            "variance_minor": int(cutover["successor_total_minor"])
            - int(cutover["prior_value_minor"]),
            "successor_account_ids": [str(row["successor_account_id"]) for row in successors],
        }

    def _create_account_budget_link(
        self,
        connection: Any,
        account_id: str,
        category_id: str,
        link_behavior: str,
        derivation_method: str,
        now: datetime,
        *,
        effective_date: date | None = None,
    ) -> None:
        insert_version(
            connection,
            "account_budget_links",
            {
                "account_id": account_id,
                "category_id": category_id,
                "link_behavior": link_behavior,
                "derivation_method": derivation_method,
                "effective_date": effective_date or now.date(),
                "valid_from": now,
                "valid_to": MAX_TS,
                "created_at": now,
                "created_by_user_id": None,
            },
        )

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
