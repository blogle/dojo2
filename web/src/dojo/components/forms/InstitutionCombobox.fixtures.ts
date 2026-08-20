import { defineFixtures } from "@/dojo/components/fixtures";

import InstitutionCombobox from "./InstitutionCombobox.vue";

type InstitutionComboboxProps = InstanceType<
  typeof InstitutionCombobox
>["$props"];

export default defineFixtures<InstitutionComboboxProps>({
  component: InstitutionCombobox,
  title: "Institution Combobox",
  description:
    "Free-text institution entry with curated and previously used suggestions.",
  scenarios: [
    {
      name: "suggestions",
      props: {
        modelValue: "",
        options: ["Chase", "Fidelity", "Neighborhood Credit Union"],
      },
    },
    {
      name: "custom institution",
      props: {
        modelValue: "Neighborhood Credit Union",
        options: ["Chase", "Fidelity"],
        helper: "Custom institution names are allowed",
      },
    },
    {
      name: "error",
      props: {
        modelValue: "",
        options: ["Chase", "Fidelity"],
        error: "Institution is required",
      },
    },
  ],
});
