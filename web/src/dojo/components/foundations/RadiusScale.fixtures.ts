import { defineFixtures } from "@/dojo/components/fixtures";

import RadiusScale from "./RadiusScale.vue";

type RadiusScaleProps = InstanceType<typeof RadiusScale>["$props"];

export default defineFixtures<RadiusScaleProps>({
  component: RadiusScale,
  title: "Rounded Corners",
  description: "Radius tokens presented as simple shape references.",
  scenarios: [
    {
      name: "default",
      props: {
        tokens: [
          { label: "none", token: "--radius-none" },
          { label: "all", token: "--radius-all" },
          { label: "sm", token: "--radius-sm" },
          { label: "md", token: "--radius-md" },
          { label: "lg", token: "--radius-lg" },
          { label: "xl", token: "--radius-xl" },
          { label: "full", token: "--radius-full" },
        ],
      },
    },
  ],
});
