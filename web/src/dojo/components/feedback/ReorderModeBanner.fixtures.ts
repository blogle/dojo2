import { defineFixtures } from "@/dojo/components/fixtures";

import ReorderModeBanner from "./ReorderModeBanner.vue";

type ReorderModeBannerProps = InstanceType<typeof ReorderModeBanner>["$props"];

export default defineFixtures<ReorderModeBannerProps>({
  component: ReorderModeBanner,
  title: "Reorder Mode Banner",
  description:
    "Inline banner that appears during reorder mode with status and actions.",
  scenarios: [
    {
      name: "no changes",
      props: {
        pendingCount: 0,
      },
    },
    {
      name: "with pending changes",
      props: {
        pendingCount: 3,
      },
    },
    {
      name: "custom text",
      props: {
        pendingCount: 2,
        cancelText: "Discard",
        saveText: "Apply changes",
      },
    },
  ],
});
