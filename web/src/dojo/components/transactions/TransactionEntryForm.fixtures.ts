import { defineFixtures } from "@/dojo/components/fixtures";

import TransactionEntryForm from "./TransactionEntryForm.vue";

type TransactionEntryFormProps = InstanceType<
  typeof TransactionEntryForm
>["$props"];

export default defineFixtures<TransactionEntryFormProps>({
  component: TransactionEntryForm,
  title: "Transaction Entry Form",
  description:
    "A reusable account transaction and transfer entry surface, including the canonical Uncategorized target.",
  scenarios: [
    {
      name: "budget account entry",
      props: {
        defaultAccountId: "account-maple-checking",
        accounts: [
          {
            account_id: "account-maple-checking",
            name: "Maple Checking",
            account_class: "BUDGET",
            is_hidden: false,
            is_active: true,
            budget_account_type: "DEPOSIT",
            actual_balance_minor: 250_000,
            pending_balance_minor: -3_200,
            cleared_balance_minor: 253_200,
            display_balance_minor: 250_000,
          },
        ],
        categories: [
          {
            category_id: "category-groceries",
            bucket_id: "bucket-groceries",
            group_id: "group-food",
            group_name: "Food",
            name: "Groceries",
            category_kind: "STANDARD",
            sort_order: 1,
            is_hidden: false,
            is_active: true,
            target_amount_minor: null,
            due_date_rule: null,
            goal_type: null,
            goal_amount_minor: null,
            goal_frequency: null,
            goal_due_date: null,
            available_minor: 45_000,
            month_activity_minor: -12_000,
            month_budgeted_minor: 60_000,
            starting_available_minor: 0,
            monthly_funding_minor: 60_000,
          },
        ],
      },
    },
  ],
});
