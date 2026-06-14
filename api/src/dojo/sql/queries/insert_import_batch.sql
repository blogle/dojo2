INSERT INTO import_batches (
    import_batch_id,
    spreadsheet_id,
    spreadsheet_title,
    imported_at,
    cutover_at,
    summary
) VALUES (?, ?, ?, ?, ?, CAST(? AS JSON))
