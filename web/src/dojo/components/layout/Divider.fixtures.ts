import { defineFixtures } from "@/dojo/components/fixtures";

import Divider from "./Divider.vue";

type DividerProps = InstanceType<typeof Divider>["$props"];

export default defineFixtures<DividerProps>({
  component: Divider,
  title: "Divider",
  description: "Simple rule primitive for separating adjacent content blocks.",
  scenarios: [
    {
      name: "horizontal",
      props: {
        orientation: "horizontal",
      },
    },
  ],
});
