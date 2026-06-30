import { defineFixtures } from "@/dojo/components/fixtures";

import LargeDetailModal from "./LargeDetailModal.vue";

type LargeDetailModalProps = InstanceType<typeof LargeDetailModal>["$props"];

export default defineFixtures<LargeDetailModalProps>({
  component: LargeDetailModal,
  title: "Large Detail Modal",
  description: "Large detail modal shell with header, optional tabs, scrollable body, and footer.",
  scenarios: [
    {
      name: "default",
      props: {
        contained: true,
        visible: true,
        title: "Detail view",
        subtitle: "Secondary information about the item.",
        sticky: true,
      },
      slots: {
        tabs: `
          <div style="display:flex;gap:8px;flex-wrap:wrap;">
            <span style="display:inline-flex;align-items:center;min-height:28px;padding:0 10px;border-radius:var(--radius-all);background:var(--color-primary-container);color:var(--color-on-primary-container);font-size:var(--text-label-sm-font-size);font-weight:600;">Details</span>
            <span style="display:inline-flex;align-items:center;min-height:28px;padding:0 10px;color:var(--color-primary);font-size:var(--text-label-sm-font-size);">History</span>
            <span style="display:inline-flex;align-items:center;min-height:28px;padding:0 10px;color:var(--color-primary);font-size:var(--text-label-sm-font-size);">Settings</span>
          </div>
        `,
        default: `
          <div style="display:grid;gap:16px;">
            <div style="display:grid;gap:8px;grid-template-columns:repeat(3,minmax(0,1fr));">
              <div style="padding:12px;border:1px solid var(--color-outline);background:var(--color-surface);border-radius:var(--radius-all);">Value A<br><strong>$1,200.00</strong></div>
              <div style="padding:12px;border:1px solid var(--color-outline);background:var(--color-surface);border-radius:var(--radius-all);">Value B<br><strong>$450.00</strong></div>
              <div style="padding:12px;border:1px solid var(--color-outline);background:var(--color-surface);border-radius:var(--radius-all);">Value C<br><strong>$2,800.00</strong></div>
            </div>
            <div style="padding:12px;border:1px solid var(--color-primary-container);background:var(--color-surface-selected);border-radius:var(--radius-all);">Tab content renders inside the scrollable body region.</div>
          </div>
        `,
        footer: `
          <div style="display:flex;gap:8px;justify-content:flex-end;">
            <button style="min-height:36px;padding:0 14px;border:1px solid var(--color-outline);background:var(--color-surface);color:var(--color-on-surface);border-radius:var(--radius-all);font-family:inherit;">Cancel</button>
            <button style="min-height:36px;padding:0 14px;border:1px solid transparent;background:var(--color-primary);color:var(--color-on-primary);border-radius:var(--radius-all);font-family:inherit;">Save</button>
          </div>
        `,
      },
    },
  ],
});
