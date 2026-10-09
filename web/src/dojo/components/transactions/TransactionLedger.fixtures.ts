import { defineFixtures } from "@/dojo/components/fixtures";

import TransactionLedger from "./TransactionLedger.vue";

type TransactionLedgerProps = InstanceType<typeof TransactionLedger>["$props"];

const account = {
  account_id: "account-checking",
  name: "Checking",
  account_class: "BUDGET",
  is_hidden: false,
  is_active: true,
  actual_balance_minor: 125_000,
  pending_balance_minor: 12_500,
  cleared_balance_minor: 112_500,
  display_balance_minor: 125_000,
};

export default defineFixtures<TransactionLedgerProps>({
  component: TransactionLedger,
  title: "Transaction Ledger",
  description:
    "Account-local transaction rows with settlement status separate from reconciliation change provenance.",
  scenarios: [
    {
      name: "reconciliation changes",
      props: {
        accounts: [account],
        categories: [],
        showAccountColumn: false,
        reconciliationChanges: {
          "transaction-added": { label: "Added", changedFields: [] },
          "transaction-edited": {
            label: "Edited",
            changedFields: ["amount_minor", "status"],
            details: "Last reconciled → Current: amount_minor, status",
          },
          "transaction-removed": {
            label: "Removed",
            changedFields: [],
            removed: true,
          },
        },
        transactions: [
          {
            transaction_id: "transaction-added",
            version: "2026-09-02T10:00:00Z",
            date: "2026-09-02",
            account_id: account.account_id,
            account_name: account.name,
            amount_minor: -4_250,
            category_id: null,
            category_name: null,
            system_category: null,
            status: "CLEARED",
            memo: "Market",
            is_hidden_entity: false,
          },
          {
            transaction_id: "transaction-edited",
            version: "2026-09-03T10:00:00Z",
            date: "2026-09-03",
            account_id: account.account_id,
            account_name: account.name,
            amount_minor: -6_800,
            category_id: null,
            category_name: null,
            system_category: null,
            status: "PENDING",
            memo: "Fuel",
            is_hidden_entity: false,
          },
          {
            transaction_id: "transaction-removed",
            version: "2026-09-01T10:00:00Z",
            date: "2026-09-01",
            account_id: account.account_id,
            account_name: account.name,
            amount_minor: -2_500,
            category_id: null,
            category_name: null,
            system_category: null,
            status: "CLEARED",
            memo: "Removed purchase",
            is_hidden_entity: false,
          },
          {
            transaction_id: "transaction-uncategorized",
            version: "2026-09-04T10:00:00Z",
            date: "2026-09-04",
            account_id: account.account_id,
            account_name: account.name,
            amount_minor: -3_200,
            category_id: null,
            category_name: null,
            system_category: "TX_UNCATEGORIZED",
            status: "PENDING",
            memo: "Uncategorized market purchase",
            is_hidden_entity: false,
          },
        ],
      },
    },
  ],
});
