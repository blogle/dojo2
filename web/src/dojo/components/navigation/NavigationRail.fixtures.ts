import { defineFixtures } from "@/dojo/components/fixtures";

import NavigationRail from "./NavigationRail.vue";

type NavigationRailProps = InstanceType<typeof NavigationRail>["$props"];

export default defineFixtures<NavigationRailProps>({
  component: NavigationRail,
  title: "Navigation Rail",
  description: "Generic rail primitive that can be populated with route or anchor entries.",
  scenarios: [
    {
      name: "collapsed",
      props: {
        expanded: false,
        items: [
          { kind: "route", key: "transactions", label: "Transactions", icon: "T", href: "/transactions", current: true },
          { kind: "route", key: "budget", label: "Budget", icon: "B", href: "/budget" },
          { kind: "route", key: "assets", label: "Assets", icon: "A", href: "/assets", badge: 3 },
        ],
      },
      presentation: {
        container: "none",
      },
    },
    {
      name: "expanded",
      props: {
        expanded: true,
        items: [
          { kind: "route", key: "transactions", label: "Transactions", icon: "T", href: "/transactions", current: true },
          { kind: "route", key: "budget", label: "Budget", icon: "B", href: "/budget" },
          { kind: "route", key: "assets", label: "Assets & Liabilities", icon: "A", href: "/assets", badge: 3 },
        ],
      },
      presentation: {
        container: "none",
      },
    },
  ],
});
