INSERT INTO import_runs (
    import_run_id,
    spreadsheet_id,
    spreadsheet_title,
    started_at,
    completed_at,
    status,
    source_kind,
    validation_passed,
    summary,
    validation_report,
    error_message
) VALUES (?, ?, ?, ?, ?, ?, ?, ?, CAST(? AS JSON), CAST(? AS JSON), ?)
