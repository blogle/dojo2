import { defineFixtures } from "@/dojo/components/fixtures";

import SpacingScale from "./SpacingScale.vue";

type SpacingScaleProps = InstanceType<typeof SpacingScale>["$props"];

export default defineFixtures<SpacingScaleProps>({
  component: SpacingScale,
  title: "Spacing",
  description: "",
  scenarios: [
    {
      name: "default",
      props: {
        tokens: [
          { label: "micro", token: "--space-micro" },
          { label: "xs", token: "--space-xs" },
          { label: "sm", token: "--space-sm" },
          { label: "md", token: "--space-md" },
          { label: "lg", token: "--space-lg" },
          { label: "xl", token: "--space-xl" },
          { label: "2xl", token: "--space-2xl" },
          { label: "3xl", token: "--space-3xl" },
        ],
      },
    },
  ],
});
