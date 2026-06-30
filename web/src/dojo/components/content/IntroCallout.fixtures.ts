import { defineFixtures } from "@/dojo/components/fixtures";

import IntroCallout from "./IntroCallout.vue";

type IntroCalloutProps = InstanceType<typeof IntroCallout>["$props"];

export default defineFixtures<IntroCalloutProps>({
  component: IntroCallout,
  title: "Intro Callout",
  description: "Introductory copy block used at the top of the design-system page.",
  presentation: {
    viewport: "wide",
    container: "none",
  },
  scenarios: [
    {
      name: "default",
      props: {
        eyebrow: "Design system",
        title: "A calm, compact system for dense financial workflows.",
        body: "The foundations shown here are generated from DESIGN.md and rendered with real shared components. Fixtures define representative review states for the catalog and Cypress mounts.",
      },
    },
  ],
});
