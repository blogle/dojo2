import { defineFixtures } from "@/dojo/components/fixtures";

import BalanceTrendChart from "./BalanceTrendChart.vue";
import type { BalanceTrendPoint } from "./BalanceTrendChart.vue";

type BalanceTrendChartProps = {
  points: BalanceTrendPoint[];
  period: string;
};

const points: BalanceTrendPoint[] = [
  { date: "2026-06-01", valueMinor: 520000 },
  { date: "2026-06-05", valueMinor: 545000 },
  { date: "2026-06-10", valueMinor: 470000 },
  { date: "2026-06-15", valueMinor: 610000 },
  { date: "2026-06-20", valueMinor: 585000 },
  { date: "2026-06-25", valueMinor: 690000 },
  { date: "2026-06-30", valueMinor: 684218 },
];

export default defineFixtures<BalanceTrendChartProps>({
  component: BalanceTrendChart,
  title: "BalanceTrendChart",
  description:
    "Interactive balance chart with period selection, axes, hover, and drag measurement.",
  presentation: { container: "full-width" },
  scenarios: [
    {
      name: "One month",
      props: { points, period: "1m" },
    },
  ],
});
