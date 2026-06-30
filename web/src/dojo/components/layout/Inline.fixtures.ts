import { defineFixtures } from "@/dojo/components/fixtures";

import Inline from "./Inline.vue";

type InlineProps = InstanceType<typeof Inline>["$props"];

export default defineFixtures<InlineProps>({
  component: Inline,
  title: "Inline",
  description: "Horizontal primitive for chips, actions, and compact clusters.",
  scenarios: [
    {
      name: "default",
      props: {
        gap: "var(--space-xs)",
        wrap: true,
      },
      slots: {
        default: `
          <div style="border:1px solid var(--color-outline);background:var(--color-surface);padding:0 var(--space-sm);height:28px;display:flex;align-items:center;">Item 1</div>
          <div style="border:1px solid var(--color-outline);background:var(--color-surface);padding:0 var(--space-sm);height:28px;display:flex;align-items:center;">Item 2</div>
          <div style="border:1px solid var(--color-outline);background:var(--color-surface);padding:0 var(--space-sm);height:28px;display:flex;align-items:center;">Item 3</div>
          <div style="border:1px solid var(--color-outline);background:var(--color-surface);padding:0 var(--space-sm);height:28px;display:flex;align-items:center;">Item 4</div>
        `,
      },
    },
  ],
});
