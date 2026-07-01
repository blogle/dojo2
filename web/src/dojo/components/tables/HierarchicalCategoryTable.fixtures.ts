import { defineFixtures } from "@/dojo/components/fixtures";

import HierarchicalCategoryTable from "./HierarchicalCategoryTable.vue";

type HierarchicalCategoryTableProps = InstanceType<
  typeof HierarchicalCategoryTable
>["$props"];

export default defineFixtures<HierarchicalCategoryTableProps>({
  component: HierarchicalCategoryTable,
  title: "Hierarchical Category Table",
  description:
    "Unified budget table with groups, category rows, additive states, and reorder mode support.",
  scenarios: [
    {
      name: "default",
      props: {
        expandable: true,
        columns: [
          { key: "category", label: "Category" },
          { key: "goal", label: "Goal", align: "end" },
          { key: "dueDate", label: "Due date" },
          { key: "available", label: "Available", align: "end" },
          { key: "activity", label: "Activity", align: "end" },
          { key: "budgeted", label: "Budgeted", align: "end" },
        ],
        rows: [
          {
            key: "cc-payments",
            label: "Credit Card Payments",
            group: true,
            cells: {
              goal: "",
              dueDate: "",
              available: "$120.00",
              activity: "-$80.00",
              budgeted: "$40.00",
            },
            children: [
              {
                key: "visa-payment",
                label: "Visa Payment",
                cells: {
                  goal: "",
                  dueDate: "System",
                  available: "$120.00",
                  activity: "-$80.00",
                  budgeted: "$40.00",
                },
                states: [{ label: "System", variant: "info" }],
              },
            ],
          },
          {
            key: "regular-bills",
            label: "Regular bills",
            group: true,
            cells: {
              goal: "",
              dueDate: "",
              available: "$1,244.50",
              activity: "-$640.00",
              budgeted: "$1,020.00",
            },
            children: [
              {
                key: "rent",
                label: "Rent",
                cells: {
                  goal: "$1,200.00",
                  dueDate: "Jun 01",
                  available: "$0.00",
                  activity: "-$1,200.00",
                  budgeted: "$1,200.00",
                },
              },
              {
                key: "internet",
                label: "Internet",
                cells: {
                  goal: "$65.00",
                  dueDate: "Jun 14",
                  available: "-$12.00",
                  activity: "-$65.00",
                  budgeted: "$53.00",
                },
                states: [
                  { label: "Overspent", variant: "error" },
                  { label: "Due soon", variant: "warning" },
                ],
              },
            ],
          },
          {
            key: "uncategorized",
            label: "Uncategorized",
            group: true,
            expanded: false,
            cells: {
              goal: "",
              dueDate: "",
              available: "$30.00",
              activity: "$0.00",
              budgeted: "$0.00",
            },
            children: [],
          },
        ],
      },
    },
    {
      name: "reorder mode",
      props: {
        reorderable: true,
        columns: [
          { key: "category", label: "Category" },
          { key: "available", label: "Available", align: "end" },
          { key: "budgeted", label: "Budgeted", align: "end" },
        ],
        rows: [
          {
            key: "daily-spending",
            label: "Daily spending",
            group: true,
            cells: { available: "$420.00", budgeted: "$550.00" },
            children: [
              {
                key: "groceries",
                label: "Groceries",
                cells: { available: "$245.00", budgeted: "$320.00" },
              },
              {
                key: "dining-out",
                label: "Dining out",
                cells: { available: "$175.00", budgeted: "$230.00" },
              },
            ],
          },
        ],
      },
    },
  ],
});
