from __future__ import annotations

import ast
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable

REPO_ROOT = Path(__file__).resolve().parents[3]
API_ROOT = REPO_ROOT / "api"
SRC_ROOT = API_ROOT / "src" / "dojo"
ROUTER_ROOT = SRC_ROOT / "api"
APPROVED_SQL_ROOT = SRC_ROOT / "sql"

APPROVED_DUCKDB_CONNECT = {
    "api/src/dojo/database.py",
    "api/src/dojo/migrations.py",
}

APPROVED_WALL_CLOCK = {
    "api/src/dojo/clock.py",
    "api/src/dojo/live_sheet_harness.py",
}

ALLOWED_SQL_INTERPOLATION_FILES = {
    "api/src/dojo/scd.py",
}

ALLOWED_SQL_INTERPOLATION_FUNCTIONS = {
    "_clear_domain_tables",
}

FLOAT_TYPES = {"REAL", "DOUBLE", "DOUBLE PRECISION", "FLOAT"}
INTEGER_TYPES = {"BIGINT", "INTEGER", "INT", "SMALLINT", "TINYINT"}
MONEY_COLUMN_HINT = re.compile(r"(amount|balance|budget|available|worth|spend|value|minor)", re.I)
SQL_KEYWORD = re.compile(r"\b(SELECT|INSERT|UPDATE|DELETE|CREATE|DROP|ALTER|WITH|FROM|WHERE)\b")
ROUTER_MATH_NAME = re.compile(
    r"(amount|balance|budget|minor|worth|spent|available|allocation|income)", re.I
)


@dataclass(frozen=True, slots=True)
class Violation:
    path: str
    line: int
    message: str

    def render(self) -> str:
        return f"{self.path}:{self.line}: {self.message}"


def python_files_under(path: Path) -> list[Path]:
    return sorted(file for file in path.rglob("*.py") if file.is_file())


def sql_files_under(path: Path) -> list[Path]:
    return sorted(file for file in path.rglob("*.sql") if file.is_file())


def relative(path: Path) -> str:
    try:
        return path.relative_to(REPO_ROOT).as_posix()
    except ValueError:
        return path.as_posix()


def parse_file(path: Path) -> ast.AST:
    return ast.parse(path.read_text(encoding="utf-8"), filename=relative(path))


def imported_duckdb_connect_names(tree: ast.AST) -> set[str]:
    names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "duckdb":
            for alias in node.names:
                if alias.name == "connect":
                    names.add(alias.asname or alias.name)
    return names


def imported_datetime_aliases(tree: ast.AST) -> tuple[set[str], set[str], set[str]]:
    datetime_modules: set[str] = set()
    datetime_names: set[str] = set()
    date_names: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                if alias.name == "datetime":
                    datetime_modules.add(alias.asname or alias.name)
        if isinstance(node, ast.ImportFrom) and node.module == "datetime":
            for alias in node.names:
                bound = alias.asname or alias.name
                if alias.name == "datetime":
                    datetime_names.add(bound)
                if alias.name == "date":
                    date_names.add(bound)
    return datetime_modules, datetime_names, date_names


def _is_duckdb_connect_call(node: ast.Call, imported_connect_names: set[str]) -> bool:
    if isinstance(node.func, ast.Attribute):
        return (
            isinstance(node.func.value, ast.Name)
            and node.func.value.id == "duckdb"
            and node.func.attr == "connect"
        )
    return isinstance(node.func, ast.Name) and node.func.id in imported_connect_names


def check_direct_duckdb_connect(paths: Iterable[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for path in paths:
        rel = relative(path)
        tree = parse_file(path)
        imported_connect_names = imported_duckdb_connect_names(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _is_duckdb_connect_call(node, imported_connect_names):
                if rel not in APPROVED_DUCKDB_CONNECT and not rel.startswith("api/tests/"):
                    violations.append(
                        Violation(
                            rel,
                            node.lineno,
                            "direct duckdb.connect(...) is restricted to database infrastructure and tests",
                        )
                    )
    return violations


def check_direct_wall_clock(paths: Iterable[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for path in paths:
        rel = relative(path)
        if rel in APPROVED_WALL_CLOCK or rel.startswith("api/tests/"):
            continue
        tree = parse_file(path)
        datetime_modules, datetime_names, date_names = imported_datetime_aliases(tree)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not isinstance(node.func, ast.Attribute):
                continue
            target = node.func.value
            if not isinstance(target, ast.Name):
                continue
            if target.id in datetime_modules and node.func.attr in {"now", "utcnow"}:
                violations.append(
                    Violation(
                        rel,
                        node.lineno,
                        "direct datetime wall-clock access is prohibited; use dojo.clock",
                    )
                )
            elif target.id in datetime_names and node.func.attr in {"now", "utcnow"}:
                violations.append(
                    Violation(
                        rel,
                        node.lineno,
                        "direct datetime wall-clock access is prohibited; use dojo.clock",
                    )
                )
            elif target.id in date_names and node.func.attr == "today":
                violations.append(
                    Violation(
                        rel,
                        node.lineno,
                        "direct date wall-clock access is prohibited; use dojo.clock",
                    )
                )
    return violations


def _imported_modules(tree: ast.AST) -> set[str]:
    modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            modules.add(node.module)
    return modules


def check_router_boundaries(paths: Iterable[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for path in paths:
        rel = relative(path)
        tree = parse_file(path)
        modules = _imported_modules(tree)
        if "duckdb" in modules:
            violations.append(Violation(rel, 1, "routers must not import duckdb"))
        if "dojo.sql" in modules:
            violations.append(Violation(rel, 1, "routers must not load SQL resources directly"))
        imported_connect_names = imported_duckdb_connect_names(tree)
        for node in ast.walk(tree):
            if isinstance(node, ast.Call) and _is_duckdb_connect_call(node, imported_connect_names):
                violations.append(
                    Violation(rel, node.lineno, "routers must not open DuckDB connections")
                )
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"load_sql", "render_sql"}
            ):
                violations.append(
                    Violation(rel, node.lineno, "routers must not load SQL resources directly")
                )
            if isinstance(node, ast.BinOp) and isinstance(
                node.op, ast.Add | ast.Sub | ast.Mult | ast.Div
            ):
                source = ast.get_source_segment(path.read_text(encoding="utf-8"), node) or ""
                if ROUTER_MATH_NAME.search(source):
                    violations.append(
                        Violation(
                            rel, node.lineno, "routers must not contain core financial calculations"
                        )
                    )
    return violations


def check_domain_fastapi_imports(paths: Iterable[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for path in paths:
        rel = relative(path)
        tree = parse_file(path)
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("fastapi")
            ):
                violations.append(
                    Violation(rel, node.lineno, "domain modules must not import FastAPI types")
                )
            if (
                isinstance(node, ast.ImportFrom)
                and node.module
                and node.module.startswith("starlette")
            ):
                violations.append(
                    Violation(
                        rel,
                        node.lineno,
                        "domain modules must not import Starlette request/response types",
                    )
                )
    return violations


def _string_literal(node: ast.AST) -> str | None:
    if isinstance(node, ast.Constant) and isinstance(node.value, str):
        return node.value
    return None


def _sql_call_name(node: ast.Call) -> str | None:
    if isinstance(node.func, ast.Attribute):
        return node.func.attr
    return None


def _function_name_for_node(tree: ast.AST, target: ast.AST) -> str | None:
    for node in ast.walk(tree):
        if isinstance(node, ast.FunctionDef):
            for child in ast.walk(node):
                if child is target:
                    return node.name
    return None


def check_sql_construction(paths: Iterable[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for path in paths:
        rel = relative(path)
        tree = parse_file(path)
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call):
                continue
            method = _sql_call_name(node)
            if method not in {"execute", "fetch_all", "fetch_one"} or not node.args:
                continue
            function_name = _function_name_for_node(tree, node)
            if (
                rel in ALLOWED_SQL_INTERPOLATION_FILES
                or function_name in ALLOWED_SQL_INTERPOLATION_FUNCTIONS
            ):
                continue
            query_arg = node.args[0]
            if isinstance(query_arg, ast.JoinedStr):
                violations.append(
                    Violation(
                        rel,
                        query_arg.lineno,
                        "SQL f-strings are prohibited; use SQL files and allowlisted fragments",
                    )
                )
                continue
            if isinstance(query_arg, ast.BinOp):
                violations.append(
                    Violation(
                        rel,
                        query_arg.lineno,
                        "SQL string concatenation is prohibited; use SQL files and allowlisted fragments",
                    )
                )
                continue
            query_literal = _string_literal(query_arg)
            if query_literal and SQL_KEYWORD.search(query_literal):
                violations.append(
                    Violation(
                        rel,
                        query_arg.lineno,
                        "SQL queries must live in api/src/dojo/sql/*.sql",
                    )
                )
        for node in ast.walk(tree):
            if (
                isinstance(node, ast.Call)
                and isinstance(node.func, ast.Name)
                and node.func.id in {"load_sql", "render_sql"}
            ):
                if rel.startswith("api/src/dojo/api/"):
                    violations.append(
                        Violation(rel, node.lineno, "routers must not load SQL resources directly")
                    )
    return violations


def check_sql_resource_locations(paths: Iterable[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for path in paths:
        rel = relative(path)
        if not rel.startswith("api/src/dojo/sql/"):
            violations.append(Violation(rel, 1, "SQL resources must live under api/src/dojo/sql/"))
    return violations


def check_test_only_imports(paths: Iterable[Path]) -> list[Violation]:
    violations: list[Violation] = []
    for path in paths:
        rel = relative(path)
        tree = parse_file(path)
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom) and node.module:
                if node.module == "tests" or node.module.startswith("tests."):
                    violations.append(
                        Violation(
                            rel, node.lineno, "production modules must not import test-only modules"
                        )
                    )
            if isinstance(node, ast.Import):
                for alias in node.names:
                    if alias.name == "tests" or alias.name.startswith("tests."):
                        violations.append(
                            Violation(
                                rel,
                                node.lineno,
                                "production modules must not import test-only modules",
                            )
                        )
    return violations


def check_money_schema(paths: Iterable[Path]) -> list[Violation]:
    violations: list[Violation] = []
    create_table = re.compile(r"^CREATE TABLE IF NOT EXISTS ([^(\s]+) \($")
    column = re.compile(r"^\s*([A-Za-z_][A-Za-z0-9_]*)\s+([A-Za-z ]+)")
    for path in paths:
        rel = relative(path)
        table_name: str | None = None
        for line_number, raw_line in enumerate(
            path.read_text(encoding="utf-8").splitlines(), start=1
        ):
            line = raw_line.strip()
            table_match = create_table.match(line)
            if table_match:
                table_name = table_match.group(1)
                continue
            if table_name is not None and line == ");":
                table_name = None
                continue
            if table_name is None or not line or line.startswith("CHECK "):
                continue
            column_match = column.match(raw_line)
            if column_match is None:
                continue
            column_name = column_match.group(1)
            column_type = column_match.group(2).strip().rstrip(",").upper()
            normalized_type = re.split(r"\s+", column_type, maxsplit=1)[0]
            if column_name.endswith("_minor") and normalized_type not in INTEGER_TYPES:
                violations.append(
                    Violation(
                        rel,
                        line_number,
                        f"persisted money column {table_name}.{column_name} must use an integer minor-unit type, found {column_type}",
                    )
                )
            elif MONEY_COLUMN_HINT.search(column_name) and normalized_type in FLOAT_TYPES:
                violations.append(
                    Violation(
                        rel,
                        line_number,
                        f"persisted money column {table_name}.{column_name} must not use floating-point type {column_type}",
                    )
                )
    return violations


def collect_repository_policy_violations() -> list[Violation]:
    python_files = python_files_under(SRC_ROOT)
    router_files = python_files_under(ROUTER_ROOT)
    domain_files = [
        SRC_ROOT / "service.py",
        SRC_ROOT / "aggregate_validation.py",
        SRC_ROOT / "importer.py",
    ]
    sql_files = sql_files_under(APPROVED_SQL_ROOT)

    violations = [
        *check_direct_duckdb_connect(python_files),
        *check_direct_wall_clock(python_files),
        *check_router_boundaries(router_files),
        *check_domain_fastapi_imports(domain_files),
        *check_sql_construction([SRC_ROOT / "service.py", *router_files]),
        *check_sql_resource_locations(sql_files),
        *check_test_only_imports(python_files),
        *check_money_schema(sql_files),
    ]
    return sorted(
        violations, key=lambda violation: (violation.path, violation.line, violation.message)
    )


def format_violations(violations: Iterable[Violation]) -> str:
    return "\n".join(violation.render() for violation in violations)
