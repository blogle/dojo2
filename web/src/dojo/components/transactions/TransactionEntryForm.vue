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
  submit: [payload: TransactionPayload];
}>();

const date = ref("");
const accountId = ref("");
const categoryId = ref("");
type EntryKind = "STANDARD" | "AVAILABLE_TO_BUDGET" | "ACCOUNT_TRANSFER";
const entryKind = ref<EntryKind>("STANDARD");
const amount = ref("");
const direction = ref("outflow");
const memo = ref("");

function todayString() {
  const now = new Date();
  return `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, "0")}-${String(now.getDate()).padStart(2, "0")}`;
}

function resetForm() {
  date.value = todayString();
  categoryId.value = "";
  entryKind.value = "STANDARD";
  amount.value = "";
  memo.value = "";
  direction.value = "outflow";
}

resetForm();

function handleSubmit() {
  if (!date.value || !accountId.value || !amount.value) return;
  if (entryKind.value === "STANDARD" && !categoryId.value) return;

  const amountMinor = parseMoneyInput(amount.value);
  if (amountMinor === null || amountMinor === 0) return;

  const finalAmount =
    direction.value === "outflow" ? -amountMinor : amountMinor;

  const systemCategory: TransactionSystemCategory | null =
    entryKind.value === "AVAILABLE_TO_BUDGET"
      ? "TX_AVAILABLE_TO_BUDGET"
      : entryKind.value === "ACCOUNT_TRANSFER"
        ? "TX_ACCOUNT_TRANSFER"
        : null;
  emit("submit", {
    date: date.value,
    account_id: accountId.value,
    amount_minor: finalAmount,
    category_id: systemCategory ? null : categoryId.value || null,
    system_category: systemCategory,
    status: "PENDING",
    memo: memo.value,
  });
  resetForm();
}

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
        (a.account_class === "BUDGET" ||
          (entryKind.value === "ACCOUNT_TRANSFER" &&
            a.account_class === "INVESTMENT")),
    )
    .map((a) => ({ value: a.account_id, label: a.name })),
]);

const categoryOptions = computed(() => [
  { value: "", label: "None" },
  ...props.categories
    .filter(
      (c) =>
        entryKind.value === "STANDARD" &&
        c.category_kind === "STANDARD" &&
        c.is_active &&
        !c.is_hidden,
    )
    .map((c) => ({ value: c.category_id, label: c.name })),
]);

const directionOptions = [
  { value: "outflow", label: "Outflow" },
  { value: "inflow", label: "Inflow" },
];

const entryKindOptions = [
  { value: "STANDARD", label: "Standard category" },
  { value: "AVAILABLE_TO_BUDGET", label: "Available to budget" },
  { value: "ACCOUNT_TRANSFER", label: "Account transfer" },
];

watch(entryKind, () => {
  categoryId.value = "";
  const selectedAccount = props.accounts.find(
    (account) => account.account_id === accountId.value,
  );
  if (
    selectedAccount?.account_class === "INVESTMENT" &&
    entryKind.value !== "ACCOUNT_TRANSFER"
  ) {
    accountId.value = "";
  }
});
</script>

<template>
  <div
    class="entry-form"
    data-cy="transaction-entry-form"
    @keydown="handleKeyDown"
  >
    <h3 class="entry-form__title">Add transaction</h3>
    <div class="entry-form__row">
      <DatePicker v-model="date" label="Date" />
      <SelectField
        v-model="accountId"
        label="Account"
        :options="accountOptions"
      />
      <SelectField
        v-model="entryKind"
        label="Entry type"
        :options="entryKindOptions"
      />
      <SelectField
        v-model="categoryId"
        label="Category"
        :options="categoryOptions"
      />
      <CurrencyField v-model="amount" label="Amount" placeholder="0.00" />
      <SelectField
        v-model="direction"
        label="Direction"
        :options="directionOptions"
      />
      <TextField v-model="memo" label="Memo" placeholder="e.g., Whole Foods" />
      <div class="entry-form__actions">
        <Button variant="primary" @click="handleSubmit">Add</Button>
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

.entry-form__title {
  margin: 0 0 var(--space-md);
  font-family: var(--text-heading-sm-font-family);
  font-size: var(--text-heading-sm-font-size);
  font-weight: var(--text-heading-sm-font-weight);
  color: var(--color-on-surface);
}

.entry-form__row {
  display: grid;
  grid-template-columns: 1fr 1fr 1fr 1fr 1fr 1fr auto;
  gap: var(--space-md);
  align-items: end;
}

.entry-form__actions {
  display: flex;
  gap: var(--space-sm);
}

@media (max-width: 1200px) {
  .entry-form__row {
    grid-template-columns: 1fr 1fr 1fr;
  }
}

@media (max-width: 720px) {
  .entry-form__row {
    grid-template-columns: 1fr;
  }
}
</style>
