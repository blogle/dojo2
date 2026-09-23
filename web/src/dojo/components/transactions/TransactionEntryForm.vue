<script setup lang="ts">
import { ref, computed, watch } from "vue";

import type {
  Account,
  Category,
  TransactionPayload,
  TransactionSystemCategory,
} from "../../types";
import { parseMoneyInput } from "../../utils/currency";
import Button from "../actions/Button.vue";
import DatePicker from "../forms/DatePicker.vue";
import SelectField from "../forms/SelectField.vue";
import CurrencyField from "../forms/CurrencyField.vue";
import TextField from "../forms/TextField.vue";

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
  counterparty_date: string;
  counterparty_status: "PENDING" | "CLEARED";
  counterparty_memo: string;
};

const date = ref("");
const accountId = ref("");
const categoryId = ref("");
const mode = ref<"transaction" | "transfer">("transaction");
const counterpartyAccountId = ref("");
const amount = ref("");
const direction = ref("outflow");
const memo = ref("");
const status = ref<"PENDING" | "CLEARED">("PENDING");
const counterpartyDetailsOpen = ref(false);
const counterpartyDate = ref("");
const counterpartyStatus = ref<"PENDING" | "CLEARED">("PENDING");
const counterpartyMemo = ref("");
const counterpartyOverrides = ref({ date: false, status: false, memo: false });

function todayString() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function resetForm() {
  date.value = todayString();
  categoryId.value = "";
  mode.value = "transaction";
  counterpartyAccountId.value = "";
  amount.value = "";
  memo.value = "";
  direction.value = "outflow";
  status.value = "PENDING";
  counterpartyDetailsOpen.value = false;
  counterpartyDate.value = date.value;
  counterpartyStatus.value = status.value;
  counterpartyMemo.value = memo.value;
  counterpartyOverrides.value = { date: false, status: false, memo: false };
}

resetForm();

function handleSubmit() {
  if (!date.value || !accountId.value || !amount.value) return;
  if (mode.value === "transaction" && !categoryId.value) return;
  if (mode.value === "transfer" && !counterpartyAccountId.value) return;

  const amountMinor = parseMoneyInput(amount.value);
  if (amountMinor === null || amountMinor === 0) return;

  if (mode.value === "transfer") {
    emit("submit", {
      kind: "transfer",
      date: date.value,
      from_account_id: accountId.value,
      to_account_id: counterpartyAccountId.value,
      amount_minor: amountMinor,
      status: status.value,
      memo: memo.value,
      counterparty_date: counterpartyDate.value || date.value,
      counterparty_status: counterpartyStatus.value,
      counterparty_memo: counterpartyMemo.value,
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
  if (event.key === "Enter" && !event.shiftKey) {
    event.preventDefault();
    handleSubmit();
  }
}

const accountOptions = computed(() => [
  { value: "", label: "Select account..." },
  ...props.accounts
    .filter(
      (a) =>
        a.is_active &&
        (mode.value === "transfer"
          ? a.account_class === "BUDGET" || a.account_class === "INVESTMENT"
          : a.account_class === "BUDGET"),
    )
    .map((a) => ({ value: a.account_id, label: a.name })),
]);

const categoryOptions = computed(() => [
  { value: "", label: "Select category..." },
  { value: "__available_to_budget__", label: "Available to budget" },
  ...props.categories
    .filter(
      (c) => c.category_kind === "STANDARD" && c.is_active && !c.is_hidden,
    )
    .map((c) => ({ value: c.category_id, label: c.name })),
]);

const directionOptions = [
  { value: "outflow", label: "Outflow" },
  { value: "inflow", label: "Inflow" },
];

watch(date, (value) => {
  if (!counterpartyOverrides.value.date) counterpartyDate.value = value;
});
watch(status, (value) => {
  if (!counterpartyOverrides.value.status) counterpartyStatus.value = value;
});
watch(memo, (value) => {
  if (!counterpartyOverrides.value.memo) counterpartyMemo.value = value;
});

const counterpartyOptions = computed(() => [
  { value: "", label: "Select account..." },
  ...props.accounts
    .filter(
      (account) =>
        account.is_active &&
        account.account_id !== accountId.value &&
        (account.account_class === "BUDGET" ||
          account.account_class === "INVESTMENT"),
    )
    .map((account) => ({ value: account.account_id, label: account.name })),
]);

const statusOptions = [
  { value: "PENDING", label: "Pending" },
  { value: "CLEARED", label: "Cleared" },
];

function setMode(nextMode: "transaction" | "transfer") {
  mode.value = nextMode;
  categoryId.value = "";
  if (nextMode === "transfer") {
    counterpartyOverrides.value = { date: false, status: false, memo: false };
    counterpartyDate.value = date.value;
    counterpartyStatus.value = status.value;
    counterpartyMemo.value = memo.value;
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
  counterpartyAccountId.value = "";
}
</script>

<template>
  <div
    class="entry-form"
    data-cy="transaction-entry-form"
    @keydown="handleKeyDown"
  >
    <h3 class="entry-form__title">Add transaction</h3>
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
      <SelectField
        v-model="accountId"
        :label="mode === 'transfer' ? 'From account' : 'Account'"
        :options="accountOptions"
      />
      <SelectField
        v-if="mode === 'transaction'"
        v-model="categoryId"
        label="Category"
        :options="categoryOptions"
      />
      <SelectField
        v-else
        v-model="counterpartyAccountId"
        label="Counterparty"
        :options="counterpartyOptions"
      />
      <CurrencyField v-model="amount" label="Amount" placeholder="0.00" />
      <SelectField
        v-if="mode === 'transaction'"
        v-model="direction"
        label="Direction"
        :options="directionOptions"
      />
      <TextField
        v-model="memo"
        label="Memo"
        :placeholder="
          mode === 'transfer' ? 'e.g., Moving money' : 'e.g., Whole Foods'
        "
      />
      <SelectField v-model="status" label="Status" :options="statusOptions" />
      <button
        v-if="mode === 'transfer'"
        class="entry-form__details-toggle"
        type="button"
        :aria-expanded="counterpartyDetailsOpen"
        @click="counterpartyDetailsOpen = !counterpartyDetailsOpen"
      >
        Counterparty details
      </button>
      <div class="entry-form__actions">
        <Button variant="primary" @click="handleSubmit">Add</Button>
      </div>
    </div>
    <div
      v-if="mode === 'transfer' && counterpartyDetailsOpen"
      class="entry-form__row entry-form__counterparty-row"
    >
      <DatePicker
        v-model="counterpartyDate"
        label="Counterparty posted date"
        @update:model-value="counterpartyOverrides.date = true"
      />
      <SelectField
        v-model="counterpartyStatus"
        label="Counterparty status"
        :options="statusOptions"
        @update:model-value="counterpartyOverrides.status = true"
      />
      <TextField
        v-model="counterpartyMemo"
        label="Counterparty memo"
        placeholder="Same as memo"
        @update:model-value="counterpartyOverrides.memo = true"
      />
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

.entry-form__title {
  margin: 0 0 var(--space-md);
  font-family: var(--text-heading-sm-font-family);
  font-size: var(--text-heading-sm-font-size);
  font-weight: var(--text-heading-sm-font-weight);
  color: var(--color-on-surface);
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
    minmax(90px, 0.75fr) minmax(130px, 1.2fr) minmax(100px, 0.8fr) minmax(
      130px,
      1fr
    )
    auto;
}

.entry-form__details-toggle {
  min-height: 36px;
  border: 0;
  padding: 0;
  background: transparent;
  color: var(--color-primary);
  font: inherit;
  text-align: left;
  cursor: pointer;
}

.entry-form__counterparty-row {
  margin-top: var(--space-md);
  grid-template-columns: minmax(130px, 1fr) minmax(130px, 1fr) minmax(
      180px,
      2fr
    );
}

.entry-form__actions {
  display: flex;
  gap: var(--space-sm);
}

@media (max-width: 1200px) {
  .entry-form__row,
  .entry-form__row--transaction,
  .entry-form__row--transfer {
    grid-template-columns: repeat(4, minmax(0, 1fr));
  }
}

@media (max-width: 720px) {
  .entry-form__row,
  .entry-form__row--transaction,
  .entry-form__row--transfer {
    grid-template-columns: 1fr;
  }
}
</style>
