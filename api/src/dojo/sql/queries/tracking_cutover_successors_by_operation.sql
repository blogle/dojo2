SELECT *
FROM tracking_cutover_successors
WHERE operation_id = ?
ORDER BY successor_order
