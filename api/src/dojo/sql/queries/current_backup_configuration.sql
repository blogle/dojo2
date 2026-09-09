SELECT *
FROM current_backup_configurations
ORDER BY valid_from DESC, row_id DESC
LIMIT 1
