import { defineFixtures } from "@/dojo/components/fixtures";

import ProgressBar from "./ProgressBar.vue";

type ProgressBarProps = InstanceType<typeof ProgressBar>["$props"];

export default defineFixtures<ProgressBarProps>({
  component: ProgressBar,
  title: "Progress Bar",
  description: "Horizontal progress bar for showing funding completion.",
  scenarios: [
    {
      name: "default",
      props: {
        value: 65,
      },
    },
    {
      name: "with label",
      props: {
        value: 75,
        label: "Funding progress",
        showValue: true,
      },
    },
    {
      name: "positive",
      props: {
        value: 100,
        variant: "positive",
        label: "Fully funded",
        showValue: true,
      },
    },
    {
      name: "partial",
      props: {
        value: 60,
        variant: "partial",
        label: "Partially funded",
        showValue: true,
      },
      notes: "Earth tone orange for partial funding progress.",
    },
    {
      name: "warning",
      props: {
        value: 45,
        variant: "warning",
        label: "Behind target",
        showValue: true,
      },
    },
    {
      name: "error",
      props: {
        value: 10,
        variant: "error",
        label: "At risk",
        showValue: true,
      },
    },
  ],
});
