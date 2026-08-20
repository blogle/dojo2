import { defineFixtures } from "@/dojo/components/fixtures";

import DatePicker from "./DatePicker.vue";

type DatePickerProps = InstanceType<typeof DatePicker>["$props"];

export default defineFixtures<DatePickerProps>({
  component: DatePicker,
  title: "Date Picker",
  description: "Date input with a calendar icon prefix for selecting dates.",
  scenarios: [
    {
      name: "default",
      props: {
        modelValue: "2026-06-30",
      },
    },
    {
      name: "with label",
      props: {
        modelValue: "2026-06-30",
        label: "Due date",
      },
    },
    {
      name: "with helper",
      props: {
        modelValue: "",
        label: "Target date",
        helper: "Select a date in the future",
      },
    },
    {
      name: "limited to today",
      props: {
        modelValue: "2026-06-30",
        label: "Statement date",
        max: "2026-06-30",
        helper: "Future statement dates are not allowed",
      },
    },
    {
      name: "with error",
      props: {
        modelValue: "",
        label: "Start date",
        error: "Date is required",
      },
    },
    {
      name: "disabled",
      props: {
        modelValue: "2026-06-30",
        label: "Locked date",
        disabled: true,
      },
    },
  ],
});
