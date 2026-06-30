import { defineFixtures } from "@/dojo/components/fixtures";

import Grid from "./Grid.vue";

type GridProps = InstanceType<typeof Grid>["$props"];

export default defineFixtures<GridProps>({
  component: Grid,
  title: "Grid",
  description: "",
  scenarios: [
    {
      name: "default",
      props: {
        columns: "repeat(3, minmax(0, 1fr))",
      },
      slots: {
        default: `
          <div style="border:1px solid var(--color-outline);background:var(--color-primary-container);padding:var(--space-sm);min-height:48px;text-align:center;">Card 1</div>
          <div style="border:1px solid var(--color-outline);background:var(--color-primary-container);padding:var(--space-sm);min-height:48px;text-align:center;">Card 2</div>
          <div style="border:1px solid var(--color-outline);background:var(--color-primary-container);padding:var(--space-sm);min-height:48px;text-align:center;">Card 3</div>
          <div style="border:1px solid var(--color-outline);background:var(--color-primary-container);padding:var(--space-sm);min-height:48px;text-align:center;">Card 4</div>
          <div style="border:1px solid var(--color-outline);background:var(--color-primary-container);padding:var(--space-sm);min-height:48px;text-align:center;">Card 5</div>
          <div style="border:1px solid var(--color-outline);background:var(--color-primary-container);padding:var(--space-sm);min-height:48px;text-align:center;">Card 6</div>
        `,
      },
    },
  ],
});
