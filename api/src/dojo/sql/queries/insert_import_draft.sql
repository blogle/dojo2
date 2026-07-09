INSERT INTO import_drafts
    (draft_id, created_at, source_kind, spreadsheet_id,
     spreadsheet_title, payload, preview, status)
VALUES (?, ?, ?, ?, ?, ?, ?, 'pending')
