import { defineFixtures } from "@/dojo/components/fixtures";

import Surface from "./Surface.vue";

type SurfaceProps = InstanceType<typeof Surface>["$props"];

export default defineFixtures<SurfaceProps>({
  component: Surface,
  title: "Surface",
  description: "",
  scenarios: [
    {
      name: "paper",
      props: {
        variant: "paper",
        padding: "var(--space-xs) var(--space-sm)",
      },
      slots: {
        default: `<strong>Paper</strong>`,
      },
      presentation: {
        container: "none",
      },
    },
    {
      name: "muted",
      props: {
        variant: "muted",
        padding: "var(--space-xs) var(--space-sm)",
      },
      slots: {
        default: `<strong>Muted</strong>`,
      },
      presentation: {
        container: "none",
      },
    },
    {
      name: "raised",
      props: {
        variant: "raised",
        padding: "var(--space-xs) var(--space-sm)",
      },
      slots: {
        default: `<strong>Raised</strong>`,
      },
      presentation: {
        container: "none",
      },
    },
  ],
});
