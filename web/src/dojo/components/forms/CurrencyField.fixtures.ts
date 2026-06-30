import { defineFixtures } from "@/dojo/components/fixtures";

import CurrencyField from "./CurrencyField.vue";

type CurrencyFieldProps = InstanceType<typeof CurrencyField>["$props"];

export default defineFixtures<CurrencyFieldProps>({
  component: CurrencyField,
  title: "Currency Field",
  description: "Money input with a fixed currency prefix for funding and goal forms.",
  scenarios: [
    {
      name: "default",
      props: {
        label: "Amount",
        modelValue: "125.00",
        helper: "Displays tabular numeric values while keeping the input height aligned with other controls.",
      },
    },
  ],
});
