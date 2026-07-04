<script setup lang="ts">
import { computed, ref, onMounted, onUnmounted } from "vue";
import { useVirtualizer, type VirtualItem } from "@tanstack/vue-virtual";

import type {
  Account,
  Category,
  Transaction,
  TransactionPayload,
} from "../../types";
import { formatCurrency, parseMoneyInput } from "../../utils/currency";
import SelectField from "../forms/SelectField.vue";
import CurrencyField from "../forms/CurrencyField.vue";
import TextField from "../forms/TextField.vue";
import DatePicker from "../forms/DatePicker.vue";
import StateBadge from "../display/StateBadge.vue";

const props = defineProps<{
  transactions: Transaction[];
  accounts: Account[];
  categories: Category[];
}>();

const emit = defineEmits<{
  commit: [id: string, payload: TransactionPayload];
  remove: [tx: Transaction];
}>();

const editingId = ref<string | null>(null);
const editDate = ref("");
const editAccountId = ref("");
const editCategoryId = ref("");
const editAmount = ref("");
const editDirection = ref("outflow");
const editStatus = ref<"PENDING" | "CLEARED">("PENDING");
const editMemo = ref("");
const scrollElement = ref<HTMLElement | null>(null);
const rowRefs = ref<Map<string, HTMLTableRowElement>>(new Map());

const rowVirtualizer = useVirtualizer(
  computed(() => ({
    count: props.transactions.length,
    getScrollElement: () => scrollElement.value,
    estimateSize: () => 42,
    overscan: 120,
    getItemKey: (index) =>
      props.transactions[index]?.transaction_id ?? `transaction-${index}`,
  })),
);

const virtualRows = computed(() => rowVirtualizer.value.getVirtualItems());
const totalRowsHeight = computed(() => rowVirtualizer.value.getTotalSize());

const virtualTransactionRows = computed<
  { virtualRow: VirtualItem; tx: Transaction }[]
>(() =>
  virtualRows.value.flatMap((virtualRow) => {
    const tx = props.transactions[virtualRow.index];
    return tx ? [{ virtualRow, tx }] : [];
  }),
);

function startEdit(tx: Transaction) {
  editingId.value = tx.transaction_id;
  editDate.value = tx.date;
  editAccountId.value = tx.account_id;
  editCategoryId.value = tx.category_id ?? "";
  const absAmount = Math.abs(tx.amount_minor) / 100;
  editAmount.value = absAmount > 0 ? absAmount.toFixed(2) : "";
  editDirection.value = tx.amount_minor >= 0 ? "inflow" : "outflow";
  editStatus.value = tx.status;
  editMemo.value = tx.memo;
}

function buildPayload(tx: Transaction): TransactionPayload | null {
  const amountMinor = parseMoneyInput(editAmount.value);
  if (amountMinor === null) return null;
  const finalAmount =
    editDirection.value === "outflow" ? -amountMinor : amountMinor;
  return {
    date: editDate.value,
    account_id: editAccountId.value,
    amount_minor: finalAmount,
    category_id: editCategoryId.value || null,
    system_category: tx.system_category,
    status: editStatus.value,
    memo: editMemo.value,
  };
}

function commitEdit() {
  if (!editingId.value) return;
  const tx = props.transactions.find(
    (t) => t.transaction_id === editingId.value,
  );
  if (!tx) return;
  const payload = buildPayload(tx);
  if (!payload) return;
  if (
    payload.date === tx.date &&
    payload.account_id === tx.account_id &&
    payload.amount_minor === tx.amount_minor &&
    payload.category_id === (tx.category_id ?? null) &&
    payload.status === tx.status &&
    payload.memo === tx.memo
  ) {
    editingId.value = null;
    return;
  }
  emit("commit", editingId.value, payload);
  editingId.value = null;
}

function cancelEdit() {
  editingId.value = null;
}

function isEscape(event: KeyboardEvent): boolean {
  return event.key === "Escape" || event.code === "Escape";
}

function handleDocumentKeydown(event: KeyboardEvent) {
  if (!editingId.value) return;
  if (isEscape(event)) {
    event.stopPropagation();
    cancelEdit();
    return;
  }
  if (event.key === "Enter" && !event.shiftKey) {
    const target = event.target as HTMLElement;
    if (target && rowRefs.value.get(editingId.value ?? "")?.contains(target)) {
      event.preventDefault();
      commitEdit();
    }
  }
}

function handleDocumentKeyup(event: KeyboardEvent) {
  if (!editingId.value) return;
  if (isEscape(event)) {
    cancelEdit();
  }
}

function handleDocumentMousedown(event: MouseEvent) {
  if (!editingId.value) return;
  const target = event.target as HTMLElement;
  const row = rowRefs.value.get(editingId.value ?? "");
  if (row && row.contains(target)) return;
  commitEdit();
}

onMounted(() => {
  document.addEventListener("keydown", handleDocumentKeydown, true);
  document.addEventListener("keyup", handleDocumentKeyup, true);
  document.addEventListener("mousedown", handleDocumentMousedown, true);
});

onUnmounted(() => {
  document.removeEventListener("keydown", handleDocumentKeydown, true);
  document.removeEventListener("keyup", handleDocumentKeyup, true);
  document.removeEventListener("mousedown", handleDocumentMousedown, true);
});

function toggleStatus() {
  editStatus.value = editStatus.value === "CLEARED" ? "PENDING" : "CLEARED";
}

function setRowRef(txId: string, el: HTMLTableRowElement | null) {
  if (el) rowRefs.value.set(txId, el);
  else rowRefs.value.delete(txId);
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
    <div ref="scrollElement" class="ledger__scroll">
      <table class="ledger__table">
        <thead class="ledger__head-group">
          <tr class="ledger__header-row">
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
          </tr>
        </thead>
        <tbody class="ledger__body" :style="{ height: `${totalRowsHeight}px` }">
          <template
            v-for="{ virtualRow, tx } in virtualTransactionRows"
            :key="virtualRow.key"
          >
            <tr
              :ref="
                (el) => setRowRef(tx.transaction_id, el as HTMLTableRowElement)
              "
              class="ledger__row"
              :class="{
                'ledger__row--editing': editingId === tx.transaction_id,
              }"
              :style="{
                transform: `translateY(${virtualRow.start}px)`,
              }"
              @click="editingId !== tx.transaction_id && startEdit(tx)"
              tabindex="0"
            >
              <td class="ledger__cell ledger__cell--check">
                <template v-if="editingId === tx.transaction_id">
                  <button
                    class="ledger__remove-btn"
                    @click.stop="emit('remove', tx)"
                    type="button"
                    title="Remove transaction"
                  >
                    ×
                  </button>
                </template>
                <template v-else>
                  <span
                    class="ledger__status-dot"
                    :class="`ledger__status-dot--${tx.status.toLowerCase()}`"
                  />
                </template>
              </td>

              <template v-if="editingId === tx.transaction_id">
                <td class="ledger__cell">
                  <DatePicker v-model="editDate" />
                </td>
                <td class="ledger__cell">
                  <SelectField
                    v-model="editAccountId"
                    :options="accountOptions"
                  />
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
                  <button
                    class="ledger__status-pill"
                    :class="`ledger__status-pill--${editStatus.toLowerCase()}`"
                    @click.stop="toggleStatus"
                    type="button"
                  >
                    {{ editStatus === "CLEARED" ? "Cleared" : "Pending" }}
                  </button>
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
                    :class="[
                      'ledger__direction',
                      directionClass(tx.amount_minor),
                    ]"
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
              </template>
            </tr>
          </template>
        </tbody>
      </table>
    </div>

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
  background: var(--color-surface);
  border: 1px solid var(--color-outline);
  border-radius: var(--radius-md);
}

.ledger__scroll {
  height: clamp(320px, calc(100vh - 430px), 720px);
  overflow: auto;
  border-radius: var(--radius-md);
}

.ledger__table {
  display: grid;
  width: 100%;
  min-width: 530px;
  border-collapse: separate;
  border-spacing: 0;
}

.ledger__head-group {
  display: block;
  position: sticky;
  top: 0;
  z-index: 2;
}

.ledger__header-row,
.ledger__row {
  display: grid;
  grid-template-columns:
    28px minmax(70px, 0.6fr) minmax(70px, 0.8fr) minmax(80px, 0.9fr)
    minmax(90px, 1.1fr) minmax(60px, 0.6fr) minmax(70px, 0.6fr)
    minmax(60px, 0.5fr);
  width: 100%;
}

.ledger__body {
  display: block;
  position: relative;
}

.ledger__head {
  display: flex;
  align-items: center;
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
  justify-content: flex-end;
  text-align: right;
}

.ledger__head--check {
  width: 28px;
}

.ledger__check-spacer {
  display: inline-block;
  width: 16px;
}

.ledger__row {
  position: absolute;
  top: 0;
  left: 0;
  background: var(--color-surface);
  border-bottom: 1px solid var(--color-outline);
  transition: background var(--transition-fast) var(--transition-ease-out);
  cursor: pointer;
}

.ledger__row:hover {
  background: var(--color-surface-selected);
}

.ledger__row--editing {
  background: var(--color-primary-container);
  cursor: default;
}

.ledger__cell {
  display: flex;
  align-items: center;
  height: 42px;
  padding: 0 12px;
  color: var(--color-on-surface);
  font-family: var(--text-body-md-font-family);
  font-size: var(--text-body-md-font-size);
  font-weight: var(--text-body-md-font-weight);
  line-height: var(--text-body-md-line-height);
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.ledger__cell--check {
  width: 28px;
  padding: 0 8px;
}

.ledger__cell--end {
  justify-content: flex-end;
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

.ledger__row--editing .ledger__cell {
  padding: 0 6px;
}

.ledger__row--editing .ledger__cell :deep(.field),
.ledger__row--editing .ledger__cell :deep(.select-field),
.ledger__row--editing .ledger__cell :deep(.field__control-shell),
.ledger__row--editing .ledger__cell :deep(.select-field__control-shell),
.ledger__row--editing .ledger__cell :deep(.field__control),
.ledger__row--editing .ledger__cell :deep(.select-field__control) {
  min-width: 0;
  width: 100%;
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

.ledger__status-pill {
  display: inline-flex;
  align-items: center;
  gap: 3px;
  padding: 1px 8px;
  border-radius: 999px;
  border: 1px solid var(--color-outline);
  background: var(--color-surface);
  color: var(--color-on-surface);
  font-family: var(--text-label-sm-font-family);
  font-size: var(--text-label-sm-font-size);
  font-weight: var(--text-label-sm-font-weight);
  line-height: var(--text-label-sm-line-height);
  cursor: pointer;
  white-space: nowrap;
  overflow: hidden;
  transition:
    background var(--transition-fast) var(--transition-ease-out),
    border-color var(--transition-fast) var(--transition-ease-out);
}

.ledger__status-pill:hover {
  background: var(--color-surface-muted);
}

.ledger__status-pill--cleared {
  border-color: var(--color-positive);
  color: var(--color-positive);
}

.ledger__status-pill--pending {
  border-color: var(--color-warning);
  color: var(--color-on-surface);
}

.ledger__remove-btn {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 20px;
  height: 20px;
  border: none;
  border-radius: var(--radius-all);
  background: transparent;
  color: var(--color-on-surface-muted);
  font-size: 16px;
  line-height: 1;
  cursor: pointer;
  flex-shrink: 0;
  transition:
    background var(--transition-fast) var(--transition-ease-out),
    color var(--transition-fast) var(--transition-ease-out);
}

.ledger__remove-btn:hover {
  background: var(--color-error-container);
  color: var(--color-error);
}

@media (max-width: 720px) {
  .ledger__scroll {
    height: 55vh;
  }
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
