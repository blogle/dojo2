import { defineFixtures } from "@/dojo/components/fixtures";

import PeriodSelector from "./PeriodSelector.vue";

type PeriodSelectorProps = InstanceType<typeof PeriodSelector>["$props"];

export default defineFixtures<PeriodSelectorProps>({
  component: PeriodSelector,
  title: "Period Selector",
  description:
    "Preset period selection used for metric and page-level summary controls.",
  presentation: {
    container: "none",
  },
  scenarios: [
    {
      name: "default",
      props: {
        modelValue: "1m",
      },
    },
    {
      name: "with comparison",
      props: {
        modelValue: "ytd",
        comparison: true,
      },
    },
  ],
});
