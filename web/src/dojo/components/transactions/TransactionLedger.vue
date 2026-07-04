<script setup lang="ts">
import { computed, ref } from "vue";

import type {
  Account,
  Category,
  Transaction,
  TransactionPayload,
} from "../../types";
import { formatCurrency, parseMoneyInput } from "../../utils/currency";
import Button from "../actions/Button.vue";
import SelectField from "../forms/SelectField.vue";
import CurrencyField from "../forms/CurrencyField.vue";
import TextField from "../forms/TextField.vue";
import DatePicker from "../forms/DatePicker.vue";
import StateBadge from "../display/StateBadge.vue";

const props = defineProps<{
  transactions: Transaction[];
  accounts: Account[];
  categories: Category[];
  editingTransactionId: string | null;
}>();

const emit = defineEmits<{
  edit: [tx: Transaction];
  remove: [tx: Transaction];
  toggleStatus: [tx: Transaction];
}>();

const editDate = ref("");
const editAccountId = ref("");
const editCategoryId = ref("");
const editAmount = ref("");
const editDirection = ref("outflow");
const editMemo = ref("");

function startEdit(tx: Transaction) {
  editDate.value = tx.date;
  editAccountId.value = tx.account_id;
  editCategoryId.value = tx.category_id ?? "";
  const absAmount = Math.abs(tx.amount_minor) / 100;
  editAmount.value = absAmount > 0 ? absAmount.toFixed(2) : "";
  editDirection.value = tx.amount_minor >= 0 ? "inflow" : "outflow";
  editMemo.value = tx.memo;
  emit("edit", tx);
}

function saveEdit() {
  if (!props.editingTransactionId) return;
  const amountMinor = parseMoneyInput(editAmount.value);
  if (amountMinor === null) return;
  const finalAmount =
    editDirection.value === "outflow" ? -amountMinor : amountMinor;

  const tx = props.transactions.find(
    (t) => t.transaction_id === props.editingTransactionId,
  );
  if (!tx) return;

  const payload: TransactionPayload = {
    date: editDate.value,
    account_id: editAccountId.value,
    amount_minor: finalAmount,
    category_id: editCategoryId.value || null,
    system_category: tx.system_category,
    status: tx.status,
    memo: editMemo.value,
  };
  emit("edit", { ...tx, ...payload } as Transaction);
}

function cancelEdit() {
  emit("edit", null as unknown as Transaction);
}

function formatDirection(amount: number): string {
  return amount >= 0 ? "Inflow" : "Outflow";
}

function directionClass(amount: number): string {
  return amount >= 0
    ? "ledger__direction--inflow"
    : "ledger__direction--outflow";
}

function statusVariant(status: string): "positive" | "info" {
  return status === "CLEARED" ? "positive" : "info";
}

function statusIcon(status: string): string {
  return status === "CLEARED" ? "check" : "clock";
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr + "T00:00:00");
  return d.toLocaleDateString("en-US", {
    month: "2-digit",
    day: "2-digit",
    year: "numeric",
  });
}

const accountOptions = computed(() =>
  props.accounts.map((a) => ({ value: a.account_id, label: a.name })),
);

const categoryOptions = computed(() => [
  { value: "", label: "None" },
  ...props.categories
    .filter((c) => c.is_active && !c.is_hidden)
    .map((c) => ({ value: c.category_id, label: c.name })),
]);

const directionOptions = [
  { value: "outflow", label: "Outflow" },
  { value: "inflow", label: "Inflow" },
];
</script>

<template>
  <div class="ledger" data-cy="transaction-ledger">
    <table class="ledger__table">
      <thead>
        <tr>
          <th class="ledger__head ledger__head--check">
            <span class="ledger__check-spacer" />
          </th>
          <th class="ledger__head">Date</th>
          <th class="ledger__head">Account</th>
          <th class="ledger__head">Category</th>
          <th class="ledger__head">Memo</th>
          <th class="ledger__head">Direction</th>
          <th class="ledger__head ledger__head--end">Amount</th>
          <th class="ledger__head">Status</th>
          <th class="ledger__head ledger__head--actions">Actions</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="tx in transactions"
          :key="tx.transaction_id"
          class="ledger__row"
          :class="{
            'ledger__row--editing': editingTransactionId === tx.transaction_id,
          }"
        >
          <td class="ledger__cell ledger__cell--check">
            <span
              class="ledger__status-dot"
              :class="`ledger__status-dot--${tx.status.toLowerCase()}`"
            />
          </td>

          <template v-if="editingTransactionId === tx.transaction_id">
            <td class="ledger__cell">
              <DatePicker v-model="editDate" />
            </td>
            <td class="ledger__cell">
              <SelectField v-model="editAccountId" :options="accountOptions" />
            </td>
            <td class="ledger__cell">
              <SelectField
                v-model="editCategoryId"
                :options="categoryOptions"
              />
            </td>
            <td class="ledger__cell">
              <TextField v-model="editMemo" placeholder="Memo" />
            </td>
            <td class="ledger__cell">
              <SelectField
                v-model="editDirection"
                :options="directionOptions"
              />
            </td>
            <td class="ledger__cell ledger__cell--end">
              <CurrencyField v-model="editAmount" placeholder="0.00" />
            </td>
            <td class="ledger__cell">
              <StateBadge
                :variant="statusVariant(tx.status)"
                :icon="statusIcon(tx.status)"
                size="sm"
              >
                {{ tx.status === "CLEARED" ? "Cleared" : "Pending" }}
              </StateBadge>
            </td>
            <td class="ledger__cell ledger__cell--actions">
              <div class="ledger__edit-actions">
                <Button variant="primary" size="sm" @click="saveEdit"
                  >Save</Button
                >
                <Button variant="secondary" size="sm" @click="cancelEdit"
                  >Cancel</Button
                >
              </div>
            </td>
          </template>

          <template v-else>
            <td class="ledger__cell">{{ formatDate(tx.date) }}</td>
            <td class="ledger__cell">{{ tx.account_name }}</td>
            <td class="ledger__cell">
              <span v-if="tx.category_name" class="ledger__category">
                <span class="ledger__category-icon">🏷</span>
                {{ tx.category_name }}
              </span>
              <span
                v-else-if="tx.system_category"
                class="ledger__system-category"
              >
                {{ tx.system_category }}
              </span>
              <span v-else class="ledger__no-category">—</span>
            </td>
            <td class="ledger__cell ledger__cell--muted">{{ tx.memo }}</td>
            <td class="ledger__cell">
              <span
                :class="['ledger__direction', directionClass(tx.amount_minor)]"
              >
                {{ tx.amount_minor >= 0 ? "↑" : "↓" }}
                {{ formatDirection(tx.amount_minor) }}
              </span>
            </td>
            <td class="ledger__cell ledger__cell--end ledger__cell--amount">
              {{ formatCurrency(tx.amount_minor) }}
            </td>
            <td class="ledger__cell">
              <StateBadge
                :variant="statusVariant(tx.status)"
                :icon="statusIcon(tx.status)"
                size="sm"
              >
                {{ tx.status === "CLEARED" ? "Cleared" : "Pending" }}
              </StateBadge>
            </td>
            <td class="ledger__cell ledger__cell--actions">
              <button
                class="ledger__menu-trigger"
                @click.stop="startEdit(tx)"
                title="Edit"
              >
                ⋮
              </button>
            </td>
          </template>
        </tr>
      </tbody>
    </table>

    <div class="ledger__footer">
      <span v-if="transactions.length === 0" class="ledger__empty">
        No transactions found.
      </span>
      <span v-else class="ledger__count">
        Loaded {{ transactions.length }} transactions
      </span>
    </div>
  </div>
</template>

<style scoped>
.ledger {
  width: 100%;
  overflow-x: auto;
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
}

.ledger__table {
  width: 100%;
  border-collapse: collapse;
}

.ledger__head {
  height: 34px;
  padding: 0 12px;
  background: var(--color-surface-muted);
  color: var(--color-on-surface-muted);
  text-align: left;
  white-space: nowrap;
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  letter-spacing: var(--text-label-sm-letter-spacing, 0.01em);
}

.ledger__head--end {
  text-align: right;
}

.ledger__head--check {
  width: 32px;
}

.ledger__head--actions {
  width: 60px;
}

.ledger__check-spacer {
  display: inline-block;
  width: 16px;
}

.ledger__row {
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-outline);
  transition: background var(--transition-fast) var(--transition-ease-out);
}

.ledger__row:hover {
  background: var(--color-surface-selected);
}

.ledger__row--editing {
  background: var(--color-primary-container);
}

.ledger__cell {
  height: 42px;
  padding: 0 12px;
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
  vertical-align: middle;
}

.ledger__cell--check {
  width: 32px;
  padding: 0 8px;
}

.ledger__cell--end {
  text-align: right;
}

.ledger__cell--muted {
  color: var(--color-on-surface-muted);
}

.ledger__cell--amount {
  font-feature-settings:
    "tnum" 1,
    "zero" 1;
}

.ledger__cell--actions {
  width: 60px;
  text-align: center;
}

.ledger__status-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
}

.ledger__status-dot--cleared {
  background: var(--color-positive);
}

.ledger__status-dot--pending {
  background: var(--color-warning);
}

.ledger__category {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.ledger__category-icon {
  font-size: 14px;
}

.ledger__system-category {
  color: var(--color-on-surface-muted);
  font-style: italic;
}

.ledger__no-category {
  color: var(--color-on-surface-muted);
}

.ledger__direction {
  display: inline-flex;
  align-items: center;
  gap: 4px;
}

.ledger__direction--inflow {
  color: var(--color-positive);
}

.ledger__direction--outflow {
  color: var(--color-error);
}

.ledger__menu-trigger {
  background: none;
  border: none;
  cursor: pointer;
  color: var(--color-on-surface-muted);
  font-size: 18px;
  padding: 4px 8px;
  border-radius: var(--radius-all);
}

.ledger__menu-trigger:hover {
  background: var(--color-surface-muted);
  color: var(--color-on-surface);
}

.ledger__edit-actions {
  display: flex;
  gap: var(--space-xs);
}

.ledger__footer {
  padding: var(--space-sm) var(--space-lg);
  border-top: 1px solid var(--color-outline);
}

.ledger__count,
.ledger__empty {
  font-family: var(--text-body-sm-font-family);
  font-size: var(--text-body-sm-font-size);
  color: var(--color-on-surface-muted);
}
</style>
