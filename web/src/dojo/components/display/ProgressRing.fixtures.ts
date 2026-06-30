import { defineFixtures } from "@/dojo/components/fixtures";

import ProgressRing from "./ProgressRing.vue";

type ProgressRingProps = InstanceType<typeof ProgressRing>["$props"];

export default defineFixtures<ProgressRingProps>({
  component: ProgressRing,
  title: "Progress Ring",
  description: "SVG donut/ring chart for showing goal progress.",
  scenarios: [
    {
      name: "default",
      props: {
        value: 65,
      },
    },
    {
      name: "large",
      props: {
        value: 80,
        size: 120,
        strokeWidth: 8,
        variant: "positive",
      },
    },
    {
      name: "warning",
      props: {
        value: 45,
        variant: "warning",
      },
    },
    {
      name: "error",
      props: {
        value: 15,
        variant: "error",
      },
    },
    {
      name: "full",
      props: {
        value: 100,
        variant: "positive",
      },
    },
  ],
});
