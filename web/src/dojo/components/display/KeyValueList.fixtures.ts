import { defineFixtures } from "@/dojo/components/fixtures";

import KeyValueList from "./KeyValueList.vue";

type KeyValueListProps = InstanceType<typeof KeyValueList>["$props"];

export default defineFixtures<KeyValueListProps>({
  component: KeyValueList,
  title: "Key Value List",
  description: "Definition list for rendering label-value pairs.",
  scenarios: [
    {
      name: "default",
      props: {
        items: [
          { label: "Category", value: "Groceries" },
          { label: "Budget", value: "$500.00" },
          { label: "Spent", value: "$368.00" },
        ],
      },
    },
    {
      name: "with variants",
      props: {
        items: [
          { label: "Status", value: "On track", variant: "positive" },
          { label: "Remaining", value: "$45.00", variant: "warning" },
          { label: "Over budget", value: "-$23.00", variant: "error" },
        ],
      },
    },
  ],
});
