import { defineFixtures } from "@/dojo/components/fixtures";

import DropdownButton from "./DropdownButton.vue";

type DropdownButtonProps = InstanceType<typeof DropdownButton>["$props"];

export default defineFixtures<DropdownButtonProps>({
  component: DropdownButton,
  title: "Dropdown Button",
  description:
    "Compact action button with a menu of related secondary actions.",
  presentation: {
    container: "none",
  },
  scenarios: [
    {
      name: "add menu",
      props: {
        label: "Add",
        items: [
          {
            key: "category",
            label: "Category",
            description: "Add a category inside an existing group.",
          },
          {
            key: "group",
            label: "Category group",
            description: "Create an empty group and order it later.",
          },
        ],
      },
    },
    {
      name: "secondary",
      props: {
        label: "Actions",
        variant: "secondary",
        items: [
          { key: "retired", label: "Retired categories" },
          {
            key: "restore",
            label: "Restore latest",
            disabled: true,
            description: "No recently retired categories.",
          },
        ],
      },
    },
  ],
});
