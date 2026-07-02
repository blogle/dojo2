"""Eval fixture: Ruff FBT should object to this shape."""


def build_report(rows: list[dict[str, object]], include_hidden: bool = False) -> str:
    visible_rows = rows if include_hidden else [row for row in rows if not row.get("hidden")]
    return "\n".join(str(row) for row in visible_rows)


report = build_report(load_rows(), True)
