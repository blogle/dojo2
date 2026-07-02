import { defineFixtures } from "@/dojo/components/fixtures";

import PreviewBox from "./PreviewBox.vue";

type PreviewBoxProps = InstanceType<typeof PreviewBox>["$props"];

export default defineFixtures<PreviewBoxProps>({
  component: PreviewBox,
  title: "Preview Box",
  description: "Bordered box showing before/after value transitions.",
  scenarios: [
    {
      name: "default",
      slots: {
        default: "Groceries balance: $368.00 → $500.00",
      },
    },
    {
      name: "with title",
      props: {
        title: "Balance change",
      },
      slots: {
        default: "Savings balance: $1,200.00 → $1,500.00",
      },
    },
    {
      name: "multiple lines",
      props: {
        title: "Budget reallocation",
      },
      slots: {
        default:
          "<div>Groceries: $500 → $350</div><div>Dining: $200 → $350</div>",
      },
    },
  ],
});
