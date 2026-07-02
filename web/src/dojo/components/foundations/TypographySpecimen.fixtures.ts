import { defineFixtures } from "@/dojo/components/fixtures";

import TypographySpecimen from "./TypographySpecimen.vue";

type TypographySpecimenProps = InstanceType<
  typeof TypographySpecimen
>["$props"];

export default defineFixtures<TypographySpecimenProps>({
  component: TypographySpecimen,
  title: "Typography",
  description: "",
  scenarios: [
    {
      name: "default",
      props: {
        rows: [
          {
            token: "display-lg",
            label: "display-lg",
            specs: "32/700",
            sample: "Display Large",
          },
          {
            token: "headline-lg",
            label: "headline-lg",
            specs: "24/700",
            sample: "Headline Large",
          },
          {
            token: "headline-md",
            label: "headline-md",
            specs: "19/600",
            sample: "Headline Medium",
          },
          {
            token: "headline-sm",
            label: "headline-sm",
            specs: "16/600",
            sample: "Headline Small",
          },
          {
            token: "body-lg",
            label: "body-lg",
            specs: "16/400",
            sample: "The quick brown fox jumps over the lazy dog.",
          },
          {
            token: "body-md",
            label: "body-md",
            specs: "14/400",
            sample: "The quick brown fox jumps over the lazy dog.",
          },
          {
            token: "body-sm",
            label: "body-sm",
            specs: "13/400",
            sample: "The quick brown fox jumps over the lazy dog.",
          },
          {
            token: "label-lg",
            label: "label-lg",
            specs: "14/600",
            sample: "Label Large",
          },
          {
            token: "label-md",
            label: "label-md",
            specs: "13/600",
            sample: "Label Medium",
          },
          {
            token: "label-sm",
            label: "label-sm",
            specs: "12/600",
            sample: "Label Small",
          },
          {
            token: "caption",
            label: "caption",
            specs: "11/500",
            sample: "Caption",
          },
          {
            token: "metric-lg",
            label: "metric-lg",
            specs: "28/700",
            sample: "$12,345.67",
          },
          {
            token: "numeric",
            label: "numeric",
            specs: "14/500",
            sample: "$1,234.56",
          },
        ],
      },
    },
  ],
});
