import { describe, expect, it } from "vitest";

import { resolveGroupMove } from "../src/dojo/components/tables/HierarchicalCategoryTable.reorder";

describe("resolveGroupMove", () => {
  it("places a dragged group after the parent group when dropped among that group's children", () => {
    const move = resolveGroupMove(
      [
        { kind: "group", key: "monthly-bills" },
        { kind: "child", key: "rent" },
        { kind: "child", key: "electric" },
        { kind: "group", key: "expenses" },
        { kind: "group", key: "sinking-funds" },
      ],
      {
        rent: "monthly-bills",
        electric: "monthly-bills",
        groceries: "expenses",
        dining: "expenses",
        vacation: "sinking-funds",
      },
      ["monthly-bills", "sinking-funds", "expenses"],
      "expenses",
    );

    expect(move).toEqual({
      order: ["monthly-bills", "expenses", "sinking-funds"],
      targetKey: "monthly-bills",
      position: "after",
    });
  });

  it("does not move child rows between groups when resolving a group move", () => {
    const childParent = {
      rent: "monthly-bills",
      electric: "monthly-bills",
      groceries: "expenses",
      dining: "expenses",
      vacation: "sinking-funds",
    };

    resolveGroupMove(
      [
        { kind: "group", key: "monthly-bills" },
        { kind: "child", key: "rent" },
        { kind: "group", key: "expenses" },
        { kind: "group", key: "sinking-funds" },
        { kind: "child", key: "vacation" },
      ],
      childParent,
      ["monthly-bills", "expenses", "sinking-funds"],
      "expenses",
    );

    expect(childParent).toEqual({
      rent: "monthly-bills",
      electric: "monthly-bills",
      groceries: "expenses",
      dining: "expenses",
      vacation: "sinking-funds",
    });
  });

  it("places a dragged group before the first visible group", () => {
    const move = resolveGroupMove(
      [
        { kind: "group", key: "expenses" },
        { kind: "group", key: "monthly-bills" },
        { kind: "child", key: "rent" },
        { kind: "group", key: "sinking-funds" },
      ],
      { rent: "monthly-bills" },
      ["monthly-bills", "sinking-funds", "expenses"],
      "expenses",
    );

    expect(move).toEqual({
      order: ["expenses", "monthly-bills", "sinking-funds"],
      targetKey: "monthly-bills",
      position: "before",
    });
  });
});
