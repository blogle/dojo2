import { defineFixtures } from "@/dojo/components/fixtures";

import ComboboxField from "./ComboboxField.vue";

type ComboboxFieldProps = InstanceType<typeof ComboboxField>["$props"];

export default defineFixtures<ComboboxFieldProps>({
  component: ComboboxField,
  title: "Combobox Field",
  description: "Searchable entity picker with keyboard selection.",
  scenarios: [
    {
      name: "category choices",
      props: {
        label: "Category",
        modelValue: "groceries",
        options: [
          { value: "atb", label: "Available to budget" },
          { value: "groceries", label: "Groceries" },
          { value: "rent", label: "Rent" },
        ],
      },
    },
  ],
});
