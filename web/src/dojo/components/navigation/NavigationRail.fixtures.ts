import { defineFixtures } from "@/dojo/components/fixtures";

import NavigationRail from "./NavigationRail.vue";

type NavigationRailProps = InstanceType<typeof NavigationRail>["$props"];

export default defineFixtures<NavigationRailProps>({
  component: NavigationRail,
  title: "Navigation Rail",
  description:
    "Collapsible sidebar navigation with brand, primary items, and active state.",
  scenarios: [
    {
      name: "collapsed",
      props: {
        expanded: false,
        brand: "dojo",
        items: [
          {
            kind: "route",
            key: "transactions",
            label: "Transactions",
            icon: "transactions",
            href: "#",
            interactive: false,
          },
          {
            kind: "route",
            key: "budget",
            label: "Budget",
            icon: "budget",
            href: "#",
            current: true,
            interactive: false,
          },
          {
            kind: "route",
            key: "assets",
            label: "Assets",
            icon: "assets",
            href: "#",
            badge: 3,
            interactive: false,
          },
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
        brand: "dojo",
        items: [
          {
            kind: "route",
            key: "transactions",
            label: "Transactions",
            icon: "transactions",
            href: "#",
            interactive: false,
          },
          {
            kind: "route",
            key: "budget",
            label: "Budget",
            icon: "budget",
            href: "#",
            current: true,
            interactive: false,
          },
          {
            kind: "route",
            key: "assets",
            label: "Assets & Liabilities",
            icon: "assets",
            href: "#",
            badge: 3,
            interactive: false,
          },
        ],
      },
      presentation: {
        container: "none",
      },
    },
  ],
});
