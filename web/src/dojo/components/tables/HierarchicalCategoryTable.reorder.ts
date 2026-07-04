export type DragRowKind = "group" | "child";

export type DragRow = {
  key: string;
  kind: DragRowKind;
};

export type GroupMove = {
  order: string[];
  targetKey: string;
  position: "before" | "after";
};

export function resolveGroupMove(
  domRows: DragRow[],
  childParent: Record<string, string>,
  previousOrder: string[],
  movedGroupKey: string,
): GroupMove | null {
  const nextOrder: string[] = [];
  const seen = new Set<string>();

  for (const row of domRows) {
    const groupKey =
      row.kind === "group" ? row.key : (childParent[row.key] ?? null);
    if (!groupKey || seen.has(groupKey)) continue;
    seen.add(groupKey);
    nextOrder.push(groupKey);
  }

  for (const groupKey of previousOrder) {
    if (!seen.has(groupKey)) nextOrder.push(groupKey);
  }

  const movedIndex = nextOrder.indexOf(movedGroupKey);
  if (movedIndex === -1) return null;

  const targetKey = movedIndex === 0 ? nextOrder[1] : nextOrder[movedIndex - 1];
  if (!targetKey) return null;

  return {
    order: nextOrder,
    targetKey,
    position: movedIndex === 0 ? "before" : "after",
  };
}
