import { defineFixtures } from "@/dojo/components/fixtures";

import Tooltip from "./Tooltip.vue";

type TooltipProps = InstanceType<typeof Tooltip>["$props"];

export default defineFixtures<TooltipProps>({
  component: Tooltip,
  title: "Tooltip",
  description: "Simple tooltip wrapper that shows text on hover.",
  scenarios: [
    {
      name: "top",
      props: {
        text: "Helpful tip",
        position: "top",
      },
      slots: {
        default: '<button type="button">Hover me</button>',
      },
    },
    {
      name: "bottom",
      props: {
        text: "More info below",
        position: "bottom",
      },
      slots: {
        default: '<button type="button">Hover me</button>',
      },
    },
    {
      name: "left",
      props: {
        text: "Left side",
        position: "left",
      },
      slots: {
        default: '<button type="button">Hover me</button>',
      },
    },
    {
      name: "right",
      props: {
        text: "Right side",
        position: "right",
      },
      slots: {
        default: '<button type="button">Hover me</button>',
      },
    },
  ],
});
