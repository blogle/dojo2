import { defineFixtures } from "@/dojo/components/fixtures";

import TypographySpecimen from "./TypographySpecimen.vue";

type TypographySpecimenProps = InstanceType<typeof TypographySpecimen>["$props"];

export default defineFixtures<TypographySpecimenProps>({
  component: TypographySpecimen,
  title: "Typography",
  description: "Semantic text roles defined in DESIGN.md and rendered from generated tokens.",
  scenarios: [
    {
      name: "default",
      props: {
        rows: [
          { token: "display-lg", label: "Display Large", sample: "Display Large" },
          { token: "headline-lg", label: "Headline Large", sample: "Headline Large" },
          { token: "headline-md", label: "Headline Medium", sample: "Headline Medium" },
          { token: "headline-sm", label: "Headline Small", sample: "Headline Small" },
          { token: "body-lg", label: "Body Large", sample: "The quick brown fox jumps over the lazy dog." },
          { token: "body-md", label: "Body Medium", sample: "The quick brown fox jumps over the lazy dog." },
          { token: "body-sm", label: "Body Small", sample: "The quick brown fox jumps over the lazy dog." },
          { token: "label-lg", label: "Label Large", sample: "Label Large" },
          { token: "label-md", label: "Label Medium", sample: "Label Medium" },
          { token: "label-sm", label: "Label Small", sample: "Label Small" },
          { token: "caption", label: "Caption", sample: "Caption" },
          { token: "metric-lg", label: "Metric Large", sample: "$12,345.67" },
          { token: "numeric", label: "Numeric", sample: "$1,234.56" },
        ],
      },
    },
  ],
});
