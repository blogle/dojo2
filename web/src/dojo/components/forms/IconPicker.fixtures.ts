import { defineFixtures } from "@/dojo/components/fixtures";

import IconPicker from "./IconPicker.vue";

type IconPickerProps = InstanceType<typeof IconPicker>["$props"];

export default defineFixtures<IconPickerProps>({
  component: IconPicker,
  title: "IconPicker",
  description: "Category icon picker backed by the dojo SVG icon pack.",
  scenarios: [
    {
      name: "selected",
      props: {
        modelValue: "groceries",
        helper: "Use icons to make dense category tables easier to scan.",
      },
    },
    {
      name: "empty",
      props: {
        modelValue: null,
      },
    },
  ],
});
