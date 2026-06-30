import { defineFixtures } from "@/dojo/components/fixtures";

import IntroCallout from "./IntroCallout.vue";

type IntroCalloutProps = InstanceType<typeof IntroCallout>["$props"];

export default defineFixtures<IntroCalloutProps>({
  component: IntroCallout,
  title: "Intro Callout",
  description: "",
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
        body: "Foundations come from DESIGN.md tokens and shared components render the catalog directly.",
      },
    },
  ],
});
