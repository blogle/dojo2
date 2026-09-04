UPDATE import_drafts
SET status = 'committed'
WHERE draft_id = ?
  AND status = 'pending'
RETURNING draft_id
