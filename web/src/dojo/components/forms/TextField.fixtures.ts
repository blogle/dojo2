import { defineFixtures } from "@/dojo/components/fixtures";

import TextField from "./TextField.vue";

type TextFieldProps = InstanceType<typeof TextField>["$props"];

export default defineFixtures<TextFieldProps>({
  component: TextField,
  title: "Text Field",
  description: "Labeled text input with helper and error messaging.",
  scenarios: [
    {
      name: "default",
      props: {
        label: "Category group name",
        modelValue: "Household bills",
        helper: "Empty groups are valid and can stay in the hierarchy.",
      },
    },
    {
      name: "with error",
      props: {
        label: "Category name",
        modelValue: "",
        placeholder: "Enter a category name",
        error: "A category name is required.",
      },
    },
  ],
});
