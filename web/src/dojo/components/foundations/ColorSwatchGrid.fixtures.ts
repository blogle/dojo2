import { defineFixtures } from "@/dojo/components/fixtures";

import ColorSwatchGrid from "./ColorSwatchGrid.vue";

type ColorSwatchGridProps = InstanceType<typeof ColorSwatchGrid>["$props"];

export default defineFixtures<ColorSwatchGridProps>({
  component: ColorSwatchGrid,
  title: "Colors",
  description: "Rendered directly from generated color tokens.",
  scenarios: [
    {
      name: "default",
      props: {
        groups: [
          {
            name: "Core",
            swatches: [
              { label: "Primary", token: "--color-primary" },
              { label: "Primary Hover", token: "--color-primary-hover" },
              { label: "Primary Container", token: "--color-primary-container" },
              { label: "Secondary", token: "--color-secondary" },
              { label: "Accent", token: "--color-accent" },
              { label: "Background", token: "--color-background" },
              { label: "Surface", token: "--color-surface" },
            ],
          },
          {
            name: "Surface & Text",
            swatches: [
              { label: "Surface Raised", token: "--color-surface-raised" },
              { label: "Surface Muted", token: "--color-surface-muted" },
              { label: "Surface Selected", token: "--color-surface-selected" },
              { label: "On Surface", token: "--color-on-surface" },
              { label: "On Surface Muted", token: "--color-on-surface-muted" },
              { label: "Outline", token: "--color-outline" },
              { label: "Outline Strong", token: "--color-outline-strong" },
            ],
          },
          {
            name: "Semantic",
            swatches: [
              { label: "Positive", token: "--color-positive" },
              { label: "Warning", token: "--color-warning" },
              { label: "Error", token: "--color-error" },
              { label: "Info", token: "--color-info" },
              { label: "Historical", token: "--color-historical" },
              { label: "Historical Container", token: "--color-historical-container" },
            ],
          },
        ],
      },
    },
  ],
});
