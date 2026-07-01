import { defineFixtures } from "@/dojo/components/fixtures";

import StateBadge from "./StateBadge.vue";

type StateBadgeProps = InstanceType<typeof StateBadge>["$props"];

export default defineFixtures<StateBadgeProps>({
  component: StateBadge,
  title: "State Badge",
  description: "Semantic status badges with optional icon indicators for table rows, metrics, and banners.",
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
      name: "partial-funding",
      props: {
        variant: "partial-funding",
      },
      slots: {
        default: "Partially funded",
      },
      notes: "Earth tone orange for partial funding progress.",
    },
    {
      name: "with check icon",
      props: {
        variant: "positive",
        icon: "check",
      },
      slots: {
        default: "Paid",
      },
      notes: "Inline icon next to text label for row state indicators.",
    },
    {
      name: "with clock icon",
      props: {
        variant: "warning",
        icon: "clock",
      },
      slots: {
        default: "Upcoming",
      },
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
