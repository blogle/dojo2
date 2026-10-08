import { computed, ref, shallowRef } from "vue";

import { ApiError } from "../api/client";

type NoticeKind = "success" | "error";

type UndoEntry = {
  id: number;
  message: string;
  undoneMessage: string;
  undo: UndoAction;
};

type UndoAction =
  | { kind: "direct"; run: () => Promise<void> }
  | {
      kind: "versioned";
      key: string;
      cursor: { version: string };
      run: (expectedVersion: string) => Promise<string | void>;
    };

export type MutationNotice = {
  id: number;
  kind: NoticeKind;
  message: string;
  undoId?: number;
};

const undoEntries = shallowRef<UndoEntry[]>([]);
const currentNotice = shallowRef<MutationNotice | null>(null);
const undoPending = ref(false);
let nextNoticeId = 1;

export function mutationErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === "transaction_version_conflict") {
      return "This transaction changed elsewhere. Refresh it and try again.";
    }
    if (error.code === "reconciled_history_change_requires_confirmation") {
      return "This transaction belongs to a completed reconciliation. Review the account reconciliation before changing it.";
    }
    if (error.status === 422) {
      if (
        JSON.stringify(error.detail).includes(
          "Choose a category or select Uncategorized before saving.",
        )
      ) {
        return "Choose a category or select Uncategorized before saving.";
      }
      return "The change was not valid. Check the category and required fields.";
    }
    if (error.status >= 500) {
      return "Dojo could not save this change. Try again.";
    }
    if (
      error.message &&
      !error.message.startsWith("Request failed with status")
    ) {
      return error.message;
    }
  }
  if (error instanceof TypeError) {
    return "Dojo could not be reached. Check the connection and try again.";
  }
  return "Dojo could not save this change. Try again.";
}

function showLatestUndo(): void {
  const entry = undoEntries.value[undoEntries.value.length - 1];
  currentNotice.value = entry
    ? {
        id: entry.id,
        kind: "success",
        message: entry.message,
        undoId: entry.id,
      }
    : null;
}

export function notifyMutationSuccess(
  message: string,
  undo?: { undoneMessage: string; run: () => Promise<void> },
): void {
  if (undo) {
    const id = nextNoticeId++;
    undoEntries.value = [
      ...undoEntries.value,
      {
        id,
        message,
        undoneMessage: undo.undoneMessage,
        undo: { kind: "direct", run: undo.run },
      },
    ];
    showLatestUndo();
    return;
  }
  currentNotice.value = { id: nextNoticeId++, kind: "success", message };
}

export function notifyVersionedMutationSuccess(
  message: string,
  undoneMessage: string,
  action: {
    key: string;
    version: string;
    run: (expectedVersion: string) => Promise<string | void>;
  },
): void {
  const previousEntry = [...undoEntries.value]
    .reverse()
    .find(
      (entry) =>
        entry.undo.kind === "versioned" && entry.undo.key === action.key,
    );
  const cursor =
    previousEntry?.undo.kind === "versioned"
      ? previousEntry.undo.cursor
      : { version: action.version };
  cursor.version = action.version;

  const id = nextNoticeId++;
  undoEntries.value = [
    ...undoEntries.value,
    {
      id,
      message,
      undoneMessage,
      undo: {
        kind: "versioned",
        key: action.key,
        cursor,
        run: action.run,
      },
    },
  ];
  showLatestUndo();
}

export function notifyMutationError(error: unknown): void {
  currentNotice.value = {
    id: nextNoticeId++,
    kind: "error",
    message: mutationErrorMessage(error),
  };
}

export function dismissMutationNotice(): void {
  const undoId = currentNotice.value?.undoId;
  if (undoId !== undefined) {
    undoEntries.value = undoEntries.value.filter(
      (entry) => entry.id !== undoId,
    );
  }
  showLatestUndo();
}

export async function undoLatestMutation(): Promise<void> {
  const entry = undoEntries.value[undoEntries.value.length - 1];
  if (!entry || undoPending.value) return;

  undoPending.value = true;
  try {
    const nextVersion =
      entry.undo.kind === "direct"
        ? await entry.undo.run()
        : await entry.undo.run(entry.undo.cursor.version);
    if (entry.undo.kind === "versioned" && nextVersion) {
      entry.undo.cursor.version = nextVersion;
    }
    undoEntries.value = undoEntries.value.filter(
      (item) => item.id !== entry.id,
    );
    if (undoEntries.value.length) {
      showLatestUndo();
    } else {
      currentNotice.value = {
        id: nextNoticeId++,
        kind: "success",
        message: entry.undoneMessage,
      };
    }
  } catch (error) {
    undoEntries.value = undoEntries.value.filter(
      (item) => item.id !== entry.id,
    );
    notifyMutationError(error);
  } finally {
    undoPending.value = false;
  }
}

export function useMutationFeedback() {
  return {
    notice: computed(() => currentNotice.value),
    undoPending: computed(() => undoPending.value),
    dismiss: dismissMutationNotice,
    undoLatest: undoLatestMutation,
  };
}
