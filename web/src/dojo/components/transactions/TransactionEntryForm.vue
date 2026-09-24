<script setup lang="ts">
import { ref, computed, watch } from "vue";

import type {
  Account,
  Category,
  TransactionPayload,
  TransactionSystemCategory,
} from "../../types";
import { fetchTransactionMemoSuggestions } from "../../api/client";
import { parseMoneyInput } from "../../utils/currency";
import Button from "../actions/Button.vue";
import DatePicker from "../forms/DatePicker.vue";
import ComboboxField from "../forms/ComboboxField.vue";
import MemoAutocompleteField from "../forms/MemoAutocompleteField.vue";
import BinaryToggle, {
  type BinaryToggleOption,
} from "../forms/BinaryToggle.vue";
import CurrencyField from "../forms/CurrencyField.vue";

const props = defineProps<{
  accounts: Account[];
  categories: Category[];
}>();

const emit = defineEmits<{
  submit: [payload: TransactionPayload | TransferEntryPayload];
}>();

type TransferEntryPayload = {
  kind: "transfer";
  date: string;
  from_account_id: string;
  to_account_id: string;
  amount_minor: number;
  status: "PENDING" | "CLEARED";
  memo: string;
  to_account_date: string;
  to_account_status: "PENDING" | "CLEARED";
  to_account_memo: string;
};

const date = ref("");
const accountId = ref("");
const categoryId = ref("");
const mode = ref<"transaction" | "transfer">("transaction");
const toAccountId = ref("");
const amount = ref("");
const direction = ref("outflow");
const memo = ref("");
const status = ref<"PENDING" | "CLEARED">("PENDING");
const toAccountDetailsOpen = ref(false);
const toAccountDate = ref("");
const toAccountStatus = ref<"PENDING" | "CLEARED">("PENDING");
const toAccountMemo = ref("");
const toAccountOverrides = ref({ date: false, status: false, memo: false });
const memoSuggestions = ref<string[]>([]);
const toAccountMemoSuggestions = ref<string[]>([]);
let memoSearchVersion = 0;
let toAccountMemoSearchVersion = 0;

function todayString() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function resetForm() {
  date.value = todayString();
  categoryId.value = "";
  mode.value = "transaction";
  toAccountId.value = "";
  amount.value = "";
  memo.value = "";
  direction.value = "outflow";
  status.value = "PENDING";
  toAccountDetailsOpen.value = false;
  toAccountDate.value = date.value;
  toAccountStatus.value = status.value;
  toAccountMemo.value = memo.value;
  toAccountOverrides.value = { date: false, status: false, memo: false };
  memoSuggestions.value = [];
  toAccountMemoSuggestions.value = [];
  memoSearchVersion += 1;
  toAccountMemoSearchVersion += 1;
}

resetForm();

function handleSubmit() {
  if (!date.value || !accountId.value || !amount.value) return;
  if (
    !accountOptions.value.some((option) => option.value === accountId.value)
  ) {
    return;
  }
  if (
    mode.value === "transaction" &&
    !categoryOptions.value.some((option) => option.value === categoryId.value)
  ) {
    return;
  }
  if (
    mode.value === "transfer" &&
    !toAccountOptions.value.some((option) => option.value === toAccountId.value)
  ) {
    return;
  }

  const amountMinor = parseMoneyInput(amount.value);
  if (amountMinor === null || amountMinor === 0) return;

  if (mode.value === "transfer") {
    emit("submit", {
      kind: "transfer",
      date: date.value,
      from_account_id: accountId.value,
      to_account_id: toAccountId.value,
      amount_minor: amountMinor,
      status: status.value,
      memo: memo.value,
      to_account_date: toAccountDate.value || date.value,
      to_account_status: toAccountStatus.value,
      to_account_memo: toAccountMemo.value,
    });
    return;
  }

  const finalAmount =
    direction.value === "outflow" ? -amountMinor : amountMinor;

  const systemCategory: TransactionSystemCategory | null =
    categoryId.value === "__available_to_budget__"
      ? "TX_AVAILABLE_TO_BUDGET"
      : null;
  emit("submit", {
    date: date.value,
    account_id: accountId.value,
    amount_minor: finalAmount,
    category_id: systemCategory ? null : categoryId.value,
    system_category: systemCategory,
    status: status.value,
    memo: memo.value,
  });
}

defineExpose({ resetForm });

function handleKeyDown(event: KeyboardEvent) {
  if (
    !event.defaultPrevented &&
    event.key === "Enter" &&
    !event.shiftKey &&
    !(event.target instanceof HTMLButtonElement)
  ) {
    event.preventDefault();
    handleSubmit();
  }
}

const accountOptions = computed(() =>
  props.accounts
    .filter(
      (a) =>
        a.is_active &&
        (mode.value === "transfer"
          ? a.account_class === "BUDGET" || a.account_class === "INVESTMENT"
          : a.account_class === "BUDGET"),
    )
    .map((a) => ({ value: a.account_id, label: a.name })),
);

const categoryOptions = computed(() => [
  { value: "__available_to_budget__", label: "Available to budget" },
  ...props.categories
    .filter(
      (c) => c.category_kind === "STANDARD" && c.is_active && !c.is_hidden,
    )
    .map((c) => ({ value: c.category_id, label: c.name })),
]);

const directionOptions: [BinaryToggleOption, BinaryToggleOption] = [
  { value: "outflow", label: "Outflow", icon: "↓" },
  { value: "inflow", label: "Inflow", icon: "↑" },
];

watch(date, (value) => {
  if (!toAccountOverrides.value.date) toAccountDate.value = value;
});
watch(status, (value) => {
  if (!toAccountOverrides.value.status) toAccountStatus.value = value;
});
watch(memo, (value) => {
  if (!toAccountOverrides.value.memo) toAccountMemo.value = value;
});
watch(accountId, (value) => {
  if (value === toAccountId.value) toAccountId.value = "";
});

const toAccountOptions = computed(() =>
  props.accounts
    .filter(
      (account) =>
        account.is_active &&
        account.account_id !== accountId.value &&
        (account.account_class === "BUDGET" ||
          account.account_class === "INVESTMENT"),
    )
    .map((account) => ({ value: account.account_id, label: account.name })),
);

const statusOptions: [BinaryToggleOption, BinaryToggleOption] = [
  { value: "PENDING", label: "Pending" },
  { value: "CLEARED", label: "Cleared" },
];

watch([memo, accountId], ([query, selectedAccountId], _previous, onCleanup) => {
  const searchVersion = ++memoSearchVersion;
  memoSuggestions.value = [];
  const normalizedQuery = query.trim();
  if (normalizedQuery.length < 2) return;

  const timeout = setTimeout(() => {
    void fetchTransactionMemoSuggestions(
      normalizedQuery,
      selectedAccountId || undefined,
    )
      .then((suggestions) => {
        if (searchVersion === memoSearchVersion)
          memoSuggestions.value = suggestions;
      })
      .catch(() => {
        if (searchVersion === memoSearchVersion) memoSuggestions.value = [];
      });
  }, 180);
  onCleanup(() => clearTimeout(timeout));
});

watch(
  [toAccountMemo, toAccountId, toAccountDetailsOpen],
  ([query, selectedAccountId, detailsOpen], _previous, onCleanup) => {
    const searchVersion = ++toAccountMemoSearchVersion;
    toAccountMemoSuggestions.value = [];
    const normalizedQuery = query.trim();
    if (
      !detailsOpen ||
      !toAccountOverrides.value.memo ||
      normalizedQuery.length < 2
    ) {
      return;
    }

    const timeout = setTimeout(() => {
      void fetchTransactionMemoSuggestions(
        normalizedQuery,
        selectedAccountId || undefined,
      )
        .then((suggestions) => {
          if (searchVersion === toAccountMemoSearchVersion) {
            toAccountMemoSuggestions.value = suggestions;
          }
        })
        .catch(() => {
          if (searchVersion === toAccountMemoSearchVersion) {
            toAccountMemoSuggestions.value = [];
          }
        });
    }, 180);
    onCleanup(() => clearTimeout(timeout));
  },
);

function setMode(nextMode: "transaction" | "transfer") {
  mode.value = nextMode;
  categoryId.value = "";
  if (nextMode === "transfer") {
    toAccountOverrides.value = { date: false, status: false, memo: false };
    toAccountDate.value = date.value;
    toAccountStatus.value = status.value;
    toAccountMemo.value = memo.value;
  }
  const selected = props.accounts.find(
    (account) => account.account_id === accountId.value,
  );
  if (nextMode === "transaction" && selected?.account_class === "INVESTMENT") {
    accountId.value = "";
  }
  if (
    nextMode === "transfer" &&
    selected?.account_class !== "BUDGET" &&
    selected?.account_class !== "INVESTMENT"
  ) {
    accountId.value = "";
  }
  toAccountId.value = "";
}
</script>

<template>
  <div
    class="entry-form"
    data-cy="transaction-entry-form"
    @keydown="handleKeyDown"
  >
    <div class="entry-form__mode" role="group" aria-label="Entry mode">
      <Button
        :variant="mode === 'transaction' ? 'primary' : 'tertiary'"
        @click="setMode('transaction')"
        >Transaction</Button
      >
      <Button
        :variant="mode === 'transfer' ? 'primary' : 'tertiary'"
        @click="setMode('transfer')"
        >Transfer</Button
      >
    </div>
    <div class="entry-form__row" :class="`entry-form__row--${mode}`">
      <DatePicker v-model="date" label="Date" />
      <ComboboxField
        v-model="accountId"
        :label="mode === 'transfer' ? 'From account' : 'Account'"
        :options="accountOptions"
      />
      <ComboboxField
        v-if="mode === 'transaction'"
        v-model="categoryId"
        label="Category"
        :options="categoryOptions"
      />
      <ComboboxField
        v-else
        v-model="toAccountId"
        label="To account"
        :options="toAccountOptions"
      />
      <CurrencyField v-model="amount" label="Amount" placeholder="0.00" />
      <BinaryToggle
        v-if="mode === 'transaction'"
        v-model="direction"
        label="Direction"
        data-name="direction"
        kind="direction"
        :options="directionOptions"
      />
      <MemoAutocompleteField
        v-model="memo"
        label="Memo"
        :suggestions="memoSuggestions"
      />
      <BinaryToggle
        v-model="status"
        label="Status"
        data-name="status"
        kind="status"
        :options="statusOptions"
      />
      <div class="entry-form__actions">
        <Button variant="primary" @click="handleSubmit">Add</Button>
      </div>
    </div>
    <div
      v-if="mode === 'transfer'"
      class="entry-form__to-account-disclosure"
      :class="{
        'entry-form__to-account-disclosure--expanded': toAccountDetailsOpen,
      }"
      data-cy="to-account-disclosure"
    >
      <button
        class="entry-form__details-toggle"
        type="button"
        :aria-expanded="toAccountDetailsOpen"
        aria-controls="to-account-details-content"
        @click="toAccountDetailsOpen = !toAccountDetailsOpen"
      >
        <span>To account details</span>
        <span
          class="entry-form__details-chevron"
          :class="{ 'entry-form__details-chevron--open': toAccountDetailsOpen }"
          aria-hidden="true"
        >
          ⌄
        </span>
      </button>
      <div
        id="to-account-details-content"
        class="entry-form__to-account-content"
        data-cy="to-account-details-content"
        role="group"
        aria-label="To account details"
        v-show="toAccountDetailsOpen"
        :aria-hidden="!toAccountDetailsOpen"
      >
        <div class="entry-form__to-account-row">
          <DatePicker
            v-model="toAccountDate"
            label="To account posted date"
            @update:model-value="toAccountOverrides.date = true"
          />
          <BinaryToggle
            v-model="toAccountStatus"
            label="To account status"
            data-name="to-account-status"
            kind="status"
            :options="statusOptions"
            @update:model-value="toAccountOverrides.status = true"
          />
          <MemoAutocompleteField
            v-model="toAccountMemo"
            label="To account memo"
            :suggestions="toAccountMemoSuggestions"
            @update:model-value="toAccountOverrides.memo = true"
          />
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
.entry-form {
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  padding: var(--space-lg);
}

.entry-form__mode {
  display: flex;
  gap: var(--space-xs);
  margin-bottom: var(--space-md);
}

.entry-form__row {
  display: grid;
  grid-template-columns:
    minmax(95px, 0.85fr) minmax(120px, 1.15fr) minmax(120px, 1.15fr)
    minmax(90px, 0.8fr) minmax(95px, 0.8fr) minmax(130px, 1.2fr) minmax(
      100px,
      0.8fr
    )
    auto;
  gap: var(--space-md);
  align-items: end;
}

.entry-form__row--transaction {
  grid-template-columns:
    minmax(95px, 0.8fr) minmax(120px, 1.1fr) minmax(130px, 1.2fr)
    minmax(90px, 0.75fr) minmax(95px, 0.8fr) minmax(130px, 1.2fr) minmax(
      100px,
      0.8fr
    )
    auto;
}

.entry-form__row--transfer {
  grid-template-columns:
    minmax(95px, 0.8fr) minmax(120px, 1.1fr) minmax(120px, 1.1fr)
    minmax(90px, 0.75fr) minmax(130px, 1.2fr) minmax(110px, 0.9fr) auto;
}

.entry-form__to-account-disclosure {
  margin-top: var(--space-sm);
  overflow: hidden;
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
  background: var(--color-surface-raised);
}

.entry-form__details-toggle {
  display: inline-flex;
  align-items: center;
  justify-content: space-between;
  gap: var(--space-xs);
  width: 100%;
  min-height: 36px;
  border: 0;
  padding: var(--space-sm) var(--space-md);
  background: transparent;
  color: var(--color-on-surface-muted);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  text-align: left;
  cursor: pointer;
}

.entry-form__to-account-disclosure--expanded .entry-form__details-toggle {
  border-bottom: 1px solid var(--color-outline);
}

.entry-form__details-toggle:hover {
  color: var(--color-on-surface);
}

.entry-form__details-toggle:focus-visible {
  border-radius: var(--radius-all);
  outline: 2px solid var(--color-primary);
  outline-offset: 1px;
}

.entry-form__details-chevron {
  display: inline-block;
  transition: transform var(--transition-fast) var(--transition-ease-out);
}

.entry-form__details-chevron--open {
  transform: rotate(180deg);
}

.entry-form__to-account-content {
  padding: var(--space-md);
}

.entry-form__to-account-row {
  grid-template-columns: minmax(130px, 1fr) minmax(130px, 1fr) minmax(
      180px,
      2fr
    );
  display: grid;
  gap: var(--space-md);
  align-items: end;
}

.entry-form__actions {
  display: flex;
  gap: var(--space-sm);
}

@media (max-width: 1200px) {
  .entry-form__row--transaction {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .entry-form__row--transfer {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }

  .entry-form__to-account-row {
    grid-template-columns: repeat(3, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .entry-form__row--transaction,
  .entry-form__row--transfer,
  .entry-form__to-account-row {
    grid-template-columns: 1fr;
  }
}
</style>
