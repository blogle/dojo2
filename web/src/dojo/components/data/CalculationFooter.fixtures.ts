import { defineFixtures } from "@/dojo/components/fixtures";

import CalculationFooter from "./CalculationFooter.vue";

type CalculationFooterProps = InstanceType<typeof CalculationFooter>["$props"];

export default defineFixtures<CalculationFooterProps>({
  component: CalculationFooter,
  title: "Calculation Footer",
  description:
    "Sticky subtotal treatment with a clear scope label and tabular financial value.",
  scenarios: [
    {
      name: "positive total",
      props: { label: "Available to budget", value: "$685.73" },
    },
    {
      name: "negative subtotal",
      props: { label: "Groceries total", value: "-$42.18" },
    },
  ],
});
