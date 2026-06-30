import { defineFixtures } from "@/dojo/components/fixtures";

import Tabs from "./Tabs.vue";

type TabsProps = InstanceType<typeof Tabs>["$props"];

export default defineFixtures<TabsProps>({
  component: Tabs,
  title: "Tabs",
  description: "Compact in-surface navigation for detail sections and modal panes.",
  presentation: {
    container: "none",
  },
  scenarios: [
    {
      name: "detail sections",
      props: {
        modelValue: "overview",
        items: [
          { key: "overview", label: "Overview" },
          { key: "funding", label: "Funding" },
          { key: "advanced", label: "Advanced" },
        ],
      },
    },
  ],
});
