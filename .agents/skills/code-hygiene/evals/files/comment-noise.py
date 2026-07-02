"""Eval fixture: review comments for semantic value."""


def import_allocations(rows: list[AllocationRow]) -> list[Allocation]:
    allocations = []
    # Loop over rows.
    for row in rows:
        # Skip zero-dollar allocations.
        if row.amount_minor == 0:
            continue

        # Aspire emits hidden historical categories after they disappear from the visible sheet.
        # Preserve them here so account reconciliation still matches the source workbook.
        category = row.category or synthesize_hidden_category(row)

        # Append the allocation.
        allocations.append(Allocation(row.date, row.amount_minor, category))

    # Return allocations.
    return allocations
