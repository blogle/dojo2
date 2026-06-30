import { defineFixtures } from "@/dojo/components/fixtures";

import StateBadge from "./StateBadge.vue";

type StateBadgeProps = InstanceType<typeof StateBadge>["$props"];

export default defineFixtures<StateBadgeProps>({
  component: StateBadge,
  title: "State Badge",
  description: "Semantic status badges for table rows, metrics, and banners.",
  presentation: {
    container: "none",
  },
  scenarios: [
    {
      name: "positive",
      props: {
        variant: "positive",
      },
      slots: {
        default: "On track",
      },
    },
    {
      name: "warning",
      props: {
        variant: "warning",
      },
      slots: {
        default: "Due soon",
      },
    },
    {
      name: "error",
      props: {
        variant: "error",
      },
      slots: {
        default: "Overspent",
      },
      notes: "Use the paired container and text token for every semantic state.",
    },
    {
      name: "medium",
      props: {
        variant: "historical",
        size: "md",
      },
      slots: {
        default: "Viewing historical data",
      },
    },
  ],
});
