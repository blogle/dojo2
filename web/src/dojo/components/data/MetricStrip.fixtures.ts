import { defineFixtures } from "@/dojo/components/fixtures";

import MetricStrip from "./MetricStrip.vue";

type MetricStripProps = InstanceType<typeof MetricStrip>["$props"];

export default defineFixtures<MetricStripProps>({
  component: MetricStrip,
  title: "Metric Strip",
  description: "Horizontal metric row with values, deltas, status badges, and loading state.",
  scenarios: [
    {
      name: "default",
      props: {
        items: [
          {
            key: "revenue",
            label: "Revenue",
            value: "$12,450.00",
            delta: 8,
            status: { label: "On track", variant: "positive" },
          },
          {
            key: "expenses",
            label: "Expenses",
            value: "$8,200.00",
            delta: -3,
          },
          {
            key: "net",
            label: "Net",
            value: "$4,250.00",
            delta: 12,
          },
        ],
      },
    },
    {
      name: "loading",
      props: {
        scrollable: true,
        items: [
          { key: "one", label: "Metric one", loading: true },
          { key: "two", label: "Metric two", loading: true },
          { key: "three", label: "Metric three", loading: true },
        ],
      },
    },
  ],
});
