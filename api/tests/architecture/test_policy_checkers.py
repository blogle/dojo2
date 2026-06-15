from __future__ import annotations

from pathlib import Path

import pytest

from .checkers import (
    Violation,
    check_direct_duckdb_connect,
    check_direct_wall_clock,
    check_money_schema,
    check_router_boundaries,
    check_sql_construction,
    collect_repository_policy_violations,
    format_violations,
)


def write_source(tmp_path: Path, relative_path: str, source: str) -> Path:
    path = tmp_path / relative_path
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(source, encoding="utf-8")
    return path


FIXTURE_ROOT = Path(__file__).resolve().parents[1] / "fixtures"


def read_fixture(name: str) -> str:
    return (FIXTURE_ROOT / name).read_text(encoding="utf-8")


def messages(violations: list[Violation]) -> str:
    return format_violations(violations)


def test_repository_policy_checks_pass_on_current_repo() -> None:
    violations = collect_repository_policy_violations()
    assert violations == [], messages(violations)


def test_direct_duckdb_connect_checker_reports_file_and_line(tmp_path: Path) -> None:
    path = write_source(
        tmp_path,
        "api/src/dojo/bad_connect.py",
        "import duckdb\n\nconnection = duckdb.connect(':memory:')\n",
    )
    violations = check_direct_duckdb_connect([path])
    assert len(violations) == 1
    assert "bad_connect.py:3" in violations[0].render()


def test_direct_wall_clock_checker_reports_file_and_line(tmp_path: Path) -> None:
    path = write_source(
        tmp_path,
        "api/src/dojo/bad_clock.py",
        "from datetime import date\n\nvalue = date.today()\n",
    )
    violations = check_direct_wall_clock([path])
    assert len(violations) == 1
    assert "bad_clock.py:3" in violations[0].render()


def test_router_boundary_checker_catches_sql_and_math(tmp_path: Path) -> None:
    path = write_source(
        tmp_path,
        "api/src/dojo/api/bad_routes.py",
        "from dojo.sql import load_sql\n\namount_minor = inflow_minor - outflow_minor\nquery = load_sql('queries/list_accounts')\n",
    )
    violations = check_router_boundaries([path])
    rendered = messages(violations)
    assert "must not load SQL resources directly" in rendered
    assert "must not contain core financial calculations" in rendered


def test_sql_construction_checker_catches_fstrings(tmp_path: Path) -> None:
    path = write_source(
        tmp_path,
        "api/src/dojo/service.py",
        read_fixture("bad_sql_fstring_source.py.txt"),
    )
    violations = check_sql_construction([path])
    assert len(violations) == 1
    assert "SQL f-strings are prohibited" in violations[0].message


def test_money_schema_checker_catches_float_money_columns(tmp_path: Path) -> None:
    path = write_source(
        tmp_path,
        "api/src/dojo/sql/schema/bad.sql",
        read_fixture("bad_money_schema.sql"),
    )
    violations = check_money_schema([path])
    assert len(violations) == 1
    assert "budgets.amount_minor" in violations[0].message


@pytest.mark.parametrize(
    ("source", "expected_fragment"),
    [
        ("import duckdb\n", "must not import duckdb"),
        ("from dojo.sql import load_sql\n", "must not load SQL resources directly"),
    ],
)
def test_router_boundary_checker_catches_imports(
    tmp_path: Path, source: str, expected_fragment: str
) -> None:
    path = write_source(tmp_path, "api/src/dojo/api/bad_imports.py", source)
    violations = check_router_boundaries([path])
    assert expected_fragment in messages(violations)
