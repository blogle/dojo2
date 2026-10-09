import { computed, ref, shallowRef } from "vue";

import { ApiError } from "../api/client";

type NoticeKind = "success" | "error";

type UndoEntry = {
  id: number;
  message: string;
  undoneMessage: string;
  undo: UndoAction;
  retryMessage?: string;
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
  undoLabel?: string;
  confirm?: () => Promise<void>;
  cancel?: () => void;
};

const undoEntries = shallowRef<UndoEntry[]>([]);
const currentNotice = shallowRef<MutationNotice | null>(null);
const queuedConfirmations = shallowRef<MutationNotice[]>([]);
const deferredNotice = shallowRef<MutationNotice | null>(null);
const undoPending = ref(false);
const confirmationPending = ref(false);
let nextNoticeId = 1;

export function mutationErrorMessage(error: unknown): string {
  if (error instanceof ApiError) {
    if (error.code === "transaction_version_conflict") {
      return "This transaction changed elsewhere. Refresh it and try again.";
    }
    if (error.code === "reconciled_history_change_requires_confirmation") {
      return "This transaction belongs to a completed reconciliation. Changing it will affect future reconciliation results.";
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
  if (hasPendingDecision()) return;
  const entry = undoEntries.value[undoEntries.value.length - 1];
  currentNotice.value = entry
    ? {
        id: entry.id,
        kind: entry.retryMessage ? "error" : "success",
        message: entry.retryMessage ?? entry.message,
        undoId: entry.id,
        ...(entry.retryMessage ? { undoLabel: "Retry Undo" } : {}),
      }
    : null;
}

function hasPendingDecision(notice = currentNotice.value): boolean {
  return notice?.cancel !== undefined;
}

function isRetryNotice(notice = currentNotice.value): boolean {
  return notice?.undoLabel === "Retry Undo";
}

function showNextNotice(undoneMessage?: string): void {
  currentNotice.value = null;
  const nextConfirmation = queuedConfirmations.value[0];
  if (nextConfirmation) {
    queuedConfirmations.value = queuedConfirmations.value.slice(1);
    currentNotice.value = nextConfirmation;
    return;
  }
  if (undoEntries.value.length) {
    showLatestUndo();
    return;
  }
  if (deferredNotice.value) {
    currentNotice.value = deferredNotice.value;
    deferredNotice.value = null;
    return;
  }
  currentNotice.value = undoneMessage
    ? { id: nextNoticeId++, kind: "success", message: undoneMessage }
    : null;
}

function isRetryableUndoError(error: unknown): boolean {
  if (error instanceof ApiError) {
    return (
      error.status === 408 ||
      error.status === 425 ||
      error.status === 429 ||
      error.status >= 500
    );
  }
  return (
    error instanceof TypeError ||
    (typeof DOMException !== "undefined" &&
      error instanceof DOMException &&
      (error.name === "AbortError" || error.name === "TimeoutError"))
  );
}

function undoRetryMessage(error: unknown): string {
  return `Undo could not be completed. ${mutationErrorMessage(error)} Your change is still saved; retry Undo to try again.`;
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
    if (!hasPendingDecision()) showLatestUndo();
    return;
  }
  const notice = { id: nextNoticeId++, kind: "success" as const, message };
  if (hasPendingDecision() || isRetryNotice()) {
    deferredNotice.value = notice;
    return;
  }
  currentNotice.value = notice;
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
  if (!hasPendingDecision()) showLatestUndo();
}

export function notifyMutationError(error: unknown): void {
  const notice: MutationNotice = {
    id: nextNoticeId++,
    kind: "error",
    message: mutationErrorMessage(error),
  };
  if (hasPendingDecision() || isRetryNotice()) {
    deferredNotice.value = notice;
    return;
  }
  currentNotice.value = notice;
}

export function notifyReconciledHistoryConfirmation(
  confirm: () => Promise<void>,
  cancel: () => void,
): void {
  const notice: MutationNotice = {
    id: nextNoticeId++,
    kind: "error",
    message:
      "This transaction belongs to a completed reconciliation. The completed reconciliation is preserved; applying this change will affect future reconciliation results.",
    confirm,
    cancel,
  };
  if (hasPendingDecision() || isRetryNotice()) {
    queuedConfirmations.value = [...queuedConfirmations.value, notice];
    return;
  }
  currentNotice.value = notice;
}

export async function confirmMutationChange(): Promise<void> {
  const notice = currentNotice.value;
  if (!notice?.confirm || confirmationPending.value) return;

  confirmationPending.value = true;
  try {
    await notice.confirm();
    if (currentNotice.value?.id === notice.id) showNextNotice();
  } catch (error) {
    currentNotice.value = {
      id: nextNoticeId++,
      kind: "error",
      message: mutationErrorMessage(error),
      ...(notice.cancel ? { cancel: notice.cancel } : {}),
    };
  } finally {
    confirmationPending.value = false;
  }
}

export function dismissMutationNotice(): void {
  const notice = currentNotice.value;
  notice?.cancel?.();
  const undoId = notice?.undoId;
  if (undoId !== undefined) {
    undoEntries.value = undoEntries.value.filter(
      (entry) => entry.id !== undoId,
    );
  }
  showNextNotice();
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
    showNextNotice(entry.undoneMessage);
  } catch (error) {
    if (isRetryableUndoError(error)) {
      entry.retryMessage = undoRetryMessage(error);
      undoEntries.value = [...undoEntries.value];
      if (queuedConfirmations.value.length && !hasPendingDecision()) {
        showNextNotice();
      } else {
        showLatestUndo();
      }
    } else {
      undoEntries.value = undoEntries.value.filter(
        (item) => item.id !== entry.id,
      );
      if (currentNotice.value?.undoId === entry.id) {
        currentNotice.value = null;
      }
      notifyMutationError(error);
    }
  } finally {
    undoPending.value = false;
  }
}

export function useMutationFeedback() {
  return {
    notice: computed(() => currentNotice.value),
    undoPending: computed(() => undoPending.value),
    confirmationPending: computed(() => confirmationPending.value),
    dismiss: dismissMutationNotice,
    undoLatest: undoLatestMutation,
    confirmChange: confirmMutationChange,
  };
}
