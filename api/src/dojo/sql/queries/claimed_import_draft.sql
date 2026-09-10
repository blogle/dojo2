SELECT draft_id
FROM import_drafts
WHERE draft_id = ?
  AND status = 'committed'
