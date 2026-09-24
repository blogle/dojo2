import { defineFixtures } from "@/dojo/components/fixtures";

import MemoAutocompleteField from "./MemoAutocompleteField.vue";

type MemoAutocompleteFieldProps = InstanceType<
  typeof MemoAutocompleteField
>["$props"];

export default defineFixtures<MemoAutocompleteFieldProps>({
  component: MemoAutocompleteField,
  title: "Memo Autocomplete Field",
  description: "Free-form memo input with prior-memo suggestions.",
  scenarios: [
    {
      name: "free-form memo",
      props: {
        label: "Memo",
        modelValue: "Grocery market",
        suggestions: ["Grocery market", "Groceries", "Market purchase"],
      },
    },
  ],
});
