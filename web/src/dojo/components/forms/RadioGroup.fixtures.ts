import { defineFixtures } from "@/dojo/components/fixtures";

import RadioGroup from "./RadioGroup.vue";

type RadioGroupProps = InstanceType<typeof RadioGroup>["$props"];

export default defineFixtures<RadioGroupProps>({
  component: RadioGroup,
  title: "Radio Group",
  description: "Horizontal radio-button group for selecting between options.",
  scenarios: [
    {
      name: "default",
      props: {
        modelValue: "recurring",
        options: [
          { value: "one-time", label: "One-time goal" },
          { value: "recurring", label: "Recurring goal" },
          { value: "discretionary", label: "Discretionary goal" },
        ],
      },
    },
    {
      name: "with label",
      props: {
        modelValue: "recurring",
        label: "Goal type",
        options: [
          { value: "one-time", label: "One-time goal" },
          { value: "recurring", label: "Recurring goal" },
          { value: "discretionary", label: "Discretionary goal" },
        ],
      },
    },
    {
      name: "disabled",
      props: {
        modelValue: "recurring",
        disabled: true,
        options: [
          { value: "one-time", label: "One-time goal" },
          { value: "recurring", label: "Recurring goal" },
          { value: "discretionary", label: "Discretionary goal" },
        ],
      },
    },
  ],
});
