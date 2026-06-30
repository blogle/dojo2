import { defineFixtures } from "@/dojo/components/fixtures";

import FormModal from "./FormModal.vue";

type FormModalProps = InstanceType<typeof FormModal>["$props"];

export default defineFixtures<FormModalProps>({
  component: FormModal,
  title: "Form Modal",
  description: "Compact modal shell for add/edit flows with standard actions.",
  scenarios: [
    {
      name: "default",
      props: {
        contained: true,
        visible: true,
        title: "Edit item",
      },
      slots: {
        default: `
          <label style="display:grid;gap:4px;">
            <span style="font-size:var(--text-label-sm-font-size);font-weight:var(--text-label-sm-font-weight);text-transform:uppercase;color:var(--color-on-surface-muted);">Name</span>
            <input value="Example item" style="min-height:36px;padding:0 10px;border:1px solid var(--color-outline);background:var(--color-surface-raised);color:var(--color-on-surface);border-radius:var(--radius-all);font-family:inherit;font-size:inherit;" />
          </label>
          <p style="margin:0;color:var(--color-on-surface-muted);font-size:var(--text-body-sm-font-size);">Optional helper text for context.</p>
        `,
      },
    },
  ],
});
