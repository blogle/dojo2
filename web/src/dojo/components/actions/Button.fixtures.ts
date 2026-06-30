import { defineFixtures } from "@/dojo/components/fixtures";

import Button from "./Button.vue";

type ButtonProps = InstanceType<typeof Button>["$props"];

const plusIcon = `
  <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round">
    <path d="M12 5v14M5 12h14" />
  </svg>
`;

export default defineFixtures<ButtonProps>({
  component: Button,
  title: "Button",
  description: "Primary, secondary, and tertiary button grammar for page and modal actions.",
  presentation: {
    container: "none",
  },
  scenarios: [
    {
      name: "primary",
      props: {
        variant: "primary",
      },
      slots: {
        default: "Save",
      },
    },
    {
      name: "secondary compact with icon",
      props: {
        variant: "secondary",
        size: "sm",
      },
      slots: {
        icon: plusIcon,
        default: "Add",
      },
      notes: "The visual primary should be reserved for the single advancing action in a local context.",
    },
    {
      name: "tertiary",
      props: {
        variant: "tertiary",
      },
      slots: {
        default: "Cancel",
      },
    },
    {
      name: "disabled",
      props: {
        variant: "primary",
        disabled: true,
      },
      slots: {
        default: "Save",
      },
    },
  ],
});
