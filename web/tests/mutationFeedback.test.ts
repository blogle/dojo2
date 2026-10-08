import { beforeEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "../src/dojo/api/client";
import {
  mutationErrorMessage,
  notifyMutationError,
  notifyMutationSuccess,
  notifyVersionedMutationSuccess,
  undoLatestMutation,
  useMutationFeedback,
} from "../src/dojo/state/mutationFeedback";

const feedback = useMutationFeedback();

beforeEach(() => {
  while (feedback.notice.value) feedback.dismiss();
});

describe("shared mutation feedback", () => {
  it("keeps one latest notice and undoes reversible mutations in LIFO order", async () => {
    const undoOrder: string[] = [];
    notifyMutationSuccess("Transaction added", {
      undoneMessage: "Transaction addition undone",
      run: async () => {
        undoOrder.push("add");
      },
    });
    notifyMutationSuccess("Transaction updated", {
      undoneMessage: "Transaction edit undone",
      run: async () => {
        undoOrder.push("edit");
      },
    });

    expect(feedback.notice.value?.message).toBe("Transaction updated");
    expect(feedback.notice.value?.undoId).toBeDefined();

    await undoLatestMutation();
    expect(undoOrder).toEqual(["edit"]);
    expect(feedback.notice.value?.message).toBe("Transaction added");
    expect(feedback.notice.value?.undoId).toBeDefined();

    await undoLatestMutation();
    expect(undoOrder).toEqual(["edit", "add"]);
    expect(feedback.notice.value?.message).toBe("Transaction addition undone");
    expect(feedback.notice.value?.undoId).toBeUndefined();
  });

  it("announces one actionable mutation while replacing the prior surface", () => {
    notifyMutationSuccess("Transaction updated", {
      undoneMessage: "Transaction edit undone",
      run: vi.fn(async () => undefined),
    });
    notifyMutationSuccess("Transaction removed", {
      undoneMessage: "Transaction removal undone",
      run: vi.fn(async () => undefined),
    });

    expect(feedback.notice.value?.message).toBe("Transaction removed");
    expect(feedback.notice.value?.undoId).toBeDefined();
  });

  it("advances the shared version after each LIFO inverse", async () => {
    const expectedVersions: string[] = [];
    notifyVersionedMutationSuccess(
      "Transaction updated",
      "Transaction edit undone",
      {
        key: "transaction:one",
        version: "version-2",
        run: async (expectedVersion) => {
          expectedVersions.push(expectedVersion);
          return "version-3";
        },
      },
    );
    notifyVersionedMutationSuccess(
      "Transaction removed",
      "Transaction removal undone",
      {
        key: "transaction:one",
        version: "version-2",
        run: async (expectedVersion) => {
          expectedVersions.push(expectedVersion);
          return "version-4";
        },
      },
    );

    await undoLatestMutation();
    expect(feedback.notice.value?.message).toBe("Transaction updated");
    await undoLatestMutation();

    expect(expectedVersions).toEqual(["version-2", "version-4"]);
    expect(feedback.notice.value?.message).toBe("Transaction edit undone");
  });

  it("surfaces stale undo failures as an assertive error notice", async () => {
    notifyMutationSuccess("Transaction removed", {
      undoneMessage: "Transaction removal undone",
      run: async () => {
        throw new ApiError(409, {
          code: "transaction_version_conflict",
          message: "This transaction changed after it was removed.",
        });
      },
    });

    await undoLatestMutation();
    expect(feedback.notice.value).toMatchObject({
      kind: "error",
      message: "This transaction changed elsewhere. Refresh it and try again.",
    });
    expect(feedback.notice.value?.undoId).toBeUndefined();
  });

  it("turns a missing category target into actionable user copy", () => {
    expect(
      mutationErrorMessage(
        new ApiError(422, [
          {
            msg: "Choose a category or select Uncategorized before saving.",
          },
        ]),
      ),
    ).toBe("Choose a category or select Uncategorized before saving.");
  });

  it("shows async mutation failures as an error notice", () => {
    notifyMutationError(new Error("The request failed."));

    expect(feedback.notice.value).toMatchObject({
      kind: "error",
      message: "Dojo could not save this change. Try again.",
    });
  });

  it("removes the dismissed latest undo and exposes the preceding one", () => {
    notifyMutationSuccess("Transaction added", {
      undoneMessage: "Transaction addition undone",
      run: vi.fn(async () => undefined),
    });
    notifyMutationSuccess("Transaction updated", {
      undoneMessage: "Transaction edit undone",
      run: vi.fn(async () => undefined),
    });

    feedback.dismiss();

    expect(feedback.notice.value?.message).toBe("Transaction added");
    expect(feedback.notice.value?.undoId).toBeDefined();
  });
});
