import { defineFixtures } from "@/dojo/components/fixtures";

import Stack from "./Stack.vue";

type StackProps = InstanceType<typeof Stack>["$props"];

export default defineFixtures<StackProps>({
  component: Stack,
  title: "Stack",
  description: "",
  scenarios: [
    {
      name: "default",
      props: {
        gap: "var(--space-xs)",
      },
      slots: {
        default: `
          <div style="border:1px solid var(--color-outline);background:var(--color-primary-container);padding:var(--space-sm);text-align:center;">Row 1</div>
          <div style="border:1px solid var(--color-outline);background:var(--color-primary-container);padding:var(--space-sm);text-align:center;">Row 2</div>
          <div style="border:1px solid var(--color-outline);background:var(--color-primary-container);padding:var(--space-sm);text-align:center;">Row 3</div>
        `,
      },
    },
  ],
});
