UPDATE transactions SET entry_order = entry_order + 1
WHERE entry_order >= ? AND valid_to = ?
