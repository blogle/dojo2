import { defineFixtures } from "@/dojo/components/fixtures";

import BinaryToggle from "./BinaryToggle.vue";

type BinaryToggleProps = InstanceType<typeof BinaryToggle>["$props"];

export default defineFixtures<BinaryToggleProps>({
  component: BinaryToggle,
  title: "Binary Toggle",
  description: "Single current-value pill for two-state form choices.",
  scenarios: [
    {
      name: "pending status",
      props: {
        label: "Status",
        dataName: "status",
        kind: "status",
        modelValue: "PENDING",
        options: [
          { value: "PENDING", label: "Pending" },
          { value: "CLEARED", label: "Cleared" },
        ],
      },
    },
    {
      name: "outflow direction",
      props: {
        label: "Direction",
        dataName: "direction",
        kind: "direction",
        modelValue: "outflow",
        options: [
          { value: "outflow", label: "Outflow", icon: "↓" },
          { value: "inflow", label: "Inflow", icon: "↑" },
        ],
      },
    },
  ],
});
