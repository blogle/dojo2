import { defineFixtures } from "@/dojo/components/fixtures";

import SelectField from "./SelectField.vue";

type SelectFieldProps = InstanceType<typeof SelectField>["$props"];

export default defineFixtures<SelectFieldProps>({
  component: SelectField,
  title: "Select Field",
  description: "Form select for parent-group, goal frequency, and funding source choices.",
  scenarios: [
    {
      name: "default",
      props: {
        label: "Parent group",
        modelValue: "regular-bills",
        options: [
          { value: "uncategorized", label: "Uncategorized" },
          { value: "regular-bills", label: "Regular bills" },
          { value: "true-expenses", label: "True expenses" },
        ],
      },
    },
    {
      name: "with helper",
      props: {
        label: "Goal frequency",
        modelValue: "monthly",
        helper: "Recurring goals fund before discretionary goals when due dates tie.",
        options: [
          { value: "monthly", label: "Monthly" },
          { value: "quarterly", label: "Quarterly" },
          { value: "yearly", label: "Yearly" },
        ],
      },
    },
  ],
});
