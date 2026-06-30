import { defineFixtures } from "@/dojo/components/fixtures";

import Surface from "./Surface.vue";

type SurfaceProps = InstanceType<typeof Surface>["$props"];

export default defineFixtures<SurfaceProps>({
  component: Surface,
  title: "Surface",
  description: "Generic treatment primitive for paper, muted, and raised containers.",
  scenarios: [
    {
      name: "paper",
      props: {
        variant: "paper",
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
