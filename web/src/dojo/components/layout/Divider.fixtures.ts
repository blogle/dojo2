import { defineFixtures } from "@/dojo/components/fixtures";

import Divider from "./Divider.vue";

type DividerProps = InstanceType<typeof Divider>["$props"];

export default defineFixtures<DividerProps>({
  component: Divider,
  title: "Divider",
  description: "",
  scenarios: [
    {
      name: "horizontal",
      props: {
        orientation: "horizontal",
      },
    },
  ],
});
