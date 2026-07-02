import { defineFixtures } from "@/dojo/components/fixtures";

import PageHeader from "./PageHeader.vue";

type PageHeaderProps = InstanceType<typeof PageHeader>["$props"];

export default defineFixtures<PageHeaderProps>({
  component: PageHeader,
  title: "Page Header",
  description:
    "Page framing with title, subtitle, metadata, actions, and optional tabs.",
  scenarios: [
    {
      name: "default",
      props: {
        title: "Page title",
        subtitle: "Optional subtitle with supplementary context.",
        metadata: "Current view",
        primaryActions: true,
      },
      slots: {
        actions: `
          <div style="display:flex;gap:8px;flex-wrap:wrap;justify-content:flex-end;">
            <button style="min-height:36px;padding:0 14px;border:1px solid var(--color-outline);background:var(--color-surface);color:var(--color-on-surface);border-radius:var(--radius-all);font:inherit;font-size:var(--text-label-md-font-size);font-weight:var(--text-label-md-font-weight);">Secondary</button>
            <button style="min-height:36px;padding:0 14px;border:1px solid transparent;background:var(--color-primary);color:var(--color-on-primary);border-radius:var(--radius-all);font:inherit;font-size:var(--text-label-md-font-size);font-weight:var(--text-label-md-font-weight);">Primary</button>
          </div>
        `,
      },
      notes:
        "Actions share the row with the title at medium widths and stack beneath it on small screens.",
    },
    {
      name: "with tabs",
      props: {
        title: "Detail title",
        subtitle: "Section with tabbed sub-navigation.",
      },
      slots: {
        tabs: `
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <span style="display:inline-flex;align-items:center;min-height:28px;padding:0 10px;border-radius:var(--radius-all);background:var(--color-primary-container);color:var(--color-on-primary-container);font:inherit;font-size:var(--text-label-sm-font-size);font-weight:600;">First</span>
            <span style="display:inline-flex;align-items:center;min-height:28px;padding:0 10px;border-radius:var(--radius-all);color:var(--color-primary);font:inherit;font-size:var(--text-label-sm-font-size);font-weight:var(--text-label-sm-font-weight);">Second</span>
            <span style="display:inline-flex;align-items:center;min-height:28px;padding:0 10px;border-radius:var(--radius-all);color:var(--color-primary);font:inherit;font-size:var(--text-label-sm-font-size);font-weight:var(--text-label-sm-font-weight);">Third</span>
          </div>
        `,
      },
    },
  ],
});
