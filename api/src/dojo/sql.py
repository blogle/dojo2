from __future__ import annotations

from pathlib import Path

SQL_ROOT = Path(__file__).with_name("sql")


def load_sql(name: str) -> str:
    path = SQL_ROOT / f"{name}.sql"
    if not path.is_file():
        raise FileNotFoundError(f"SQL resource not found: {path}")
    return path.read_text(encoding="utf-8")


def render_sql(name: str, **replacements: str) -> str:
    return load_sql(name).format(**replacements)
