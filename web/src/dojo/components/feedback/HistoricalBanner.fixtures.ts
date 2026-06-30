import { defineFixtures } from "@/dojo/components/fixtures";

import HistoricalBanner from "./HistoricalBanner.vue";

type HistoricalBannerProps = InstanceType<typeof HistoricalBanner>["$props"];

export default defineFixtures<HistoricalBannerProps>({
  component: HistoricalBanner,
  title: "Historical Banner",
  description: "Read-only mode banner for global historical context.",
  scenarios: [
    {
      name: "read only mode",
      props: {
        description: "Showing the budget as of June 15, 2026. Editing and funding actions are disabled in this mode.",
      },
    },
  ],
});
