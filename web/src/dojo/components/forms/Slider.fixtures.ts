import { defineFixtures } from "@/dojo/components/fixtures";

import Slider from "./Slider.vue";

type SliderProps = InstanceType<typeof Slider>["$props"];

export default defineFixtures<SliderProps>({
  component: Slider,
  title: "Slider",
  description: "Range input for selecting amounts within a min/max range.",
  scenarios: [
    {
      name: "default",
      props: {
        modelValue: 50,
      },
    },
    {
      name: "with label",
      props: {
        modelValue: 500,
        label: "Target amount",
        min: 100,
        max: 1000,
        step: 50,
      },
    },
    {
      name: "with range labels",
      props: {
        modelValue: 250,
        label: "Budget",
        min: 0,
        max: 500,
        minLabel: "$0",
        maxLabel: "$500",
      },
    },
    {
      name: "disabled",
      props: {
        modelValue: 50,
        disabled: true,
        label: "Locked slider",
      },
    },
  ],
});
