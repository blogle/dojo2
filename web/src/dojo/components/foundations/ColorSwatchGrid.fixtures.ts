import { defineFixtures } from "@/dojo/components/fixtures";

import ColorSwatchGrid from "./ColorSwatchGrid.vue";

type ColorSwatchGridProps = InstanceType<typeof ColorSwatchGrid>["$props"];

export default defineFixtures<ColorSwatchGridProps>({
  component: ColorSwatchGrid,
  title: "Colors",
  description: "",
  scenarios: [
    {
      name: "default",
      props: {
        groups: [
          {
            name: "Primary",
            swatches: [
              { label: "Primary", token: "--color-primary" },
              { label: "Primary Hover", token: "--color-primary-hover" },
              { label: "Primary Active", token: "--color-primary-active" },
              { label: "On Primary", token: "--color-on-primary" },
              {
                label: "Primary Container",
                token: "--color-primary-container",
              },
              {
                label: "On Primary Container",
                token: "--color-on-primary-container",
              },
            ],
          },
          {
            name: "Secondary & Accent",
            swatches: [
              { label: "Secondary", token: "--color-secondary" },
              { label: "On Secondary", token: "--color-on-secondary" },
              { label: "Accent", token: "--color-accent" },
              { label: "On Accent", token: "--color-on-accent" },
            ],
          },
          {
            name: "Surfaces",
            swatches: [
              { label: "Background", token: "--color-background" },
              { label: "Surface", token: "--color-surface" },
              { label: "Surface Raised", token: "--color-surface-raised" },
              { label: "Surface Muted", token: "--color-surface-muted" },
              { label: "Surface Selected", token: "--color-surface-selected" },
            ],
          },
          {
            name: "Text & Borders",
            swatches: [
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
              {
                label: "Positive Container",
                token: "--color-positive-container",
              },
              { label: "Warning", token: "--color-warning" },
              {
                label: "Warning Container",
                token: "--color-warning-container",
              },
              { label: "Error", token: "--color-error" },
              { label: "Error Container", token: "--color-error-container" },
              { label: "Info", token: "--color-info" },
              { label: "Info Container", token: "--color-info-container" },
              { label: "Historical", token: "--color-historical" },
              {
                label: "Historical Container",
                token: "--color-historical-container",
              },
              { label: "Partial Funding", token: "--color-partial-funding" },
              {
                label: "Partial Funding Container",
                token: "--color-partial-funding-container",
              },
            ],
          },
          {
            name: "Overlay",
            swatches: [{ label: "Scrim", token: "--color-scrim" }],
          },
        ],
      },
    },
  ],
});
