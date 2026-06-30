import { defineFixtures } from "@/dojo/components/fixtures";

import PersistentWarningBanner from "./PersistentWarningBanner.vue";

type PersistentWarningBannerProps = InstanceType<
  typeof PersistentWarningBanner
>["$props"];

export default defineFixtures<PersistentWarningBannerProps>({
  component: PersistentWarningBanner,
  title: "Persistent Warning Banner",
  description: "Content-area banner with severity variant, optional actions, and dismiss.",
  scenarios: [
    {
      name: "warning with actions",
      props: {
        severity: "warning",
        title: "Action required.",
        description: "An issue needs attention before proceeding.",
        primaryAction: "Resolve",
        secondaryAction: "Dismiss",
      },
    },
    {
      name: "dismissible error",
      props: {
        severity: "error",
        title: "Invalid input detected.",
        description: "Review and correct the highlighted fields before saving.",
        dismissible: true,
      },
    },
  ],
});
