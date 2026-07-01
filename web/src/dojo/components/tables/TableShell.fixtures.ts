import { defineFixtures } from "@/dojo/components/fixtures";

import TableShell from "./TableShell.vue";

type TableShellProps = InstanceType<typeof TableShell>["$props"];

export default defineFixtures<TableShellProps>({
  component: TableShell,
  title: "Table Shell",
  description:
    "Shared header, row, and empty-state table styling for budget and history surfaces.",
  scenarios: [
    {
      name: "default",
      props: {
        columns: [
          { key: "date", label: "Date" },
          { key: "source", label: "Source" },
          { key: "amount", label: "Amount", align: "end" },
        ],
        rows: [
          { key: "1", date: "Jun 02", source: "Paycheck", amount: "$1,200.00" },
          { key: "2", date: "Jun 06", source: "Move funds", amount: "-$42.00" },
        ],
      },
    },
  ],
});
