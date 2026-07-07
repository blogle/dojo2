import { defineFixtures } from "@/dojo/components/fixtures";

import StackedEntityCard from "./StackedEntityCard.vue";

type StackedEntityCardProps = InstanceType<typeof StackedEntityCard>["$props"];

export default defineFixtures<StackedEntityCardProps>({
  component: StackedEntityCard,
  title: "Stacked Entity Card",
  description:
    "Entity card with name, value, delta, metadata, status badge, source-of-truth indicator, and click action.",
  scenarios: [
    {
      name: "default",
      props: {
        name: "Checking Account",
        primaryValue: "$12,345.67",
        metadata: "Chase Bank",
        sourceOfTruth: "ledger",
        clickable: true,
      },
    },
    {
      name: "with positive delta",
      props: {
        name: "Savings Account",
        primaryValue: "$45,678.90",
        delta: 1250,
        metadata: "Ally Bank",
        sourceOfTruth: "ledger",
        clickable: true,
      },
    },
    {
      name: "with negative delta",
      props: {
        name: "Credit Card",
        primaryValue: "-$2,345.67",
        delta: -500,
        metadata: "Visa",
        sourceOfTruth: "ledger",
        clickable: true,
      },
    },
    {
      name: "with status",
      props: {
        name: "Investment Account",
        primaryValue: "$125,000.00",
        delta: 5000,
        metadata: "Fidelity",
        sourceOfTruth: "valuation",
        status: {
          label: "Reconciled",
          variant: "positive",
        },
        clickable: true,
      },
    },
    {
      name: "with warning status",
      props: {
        name: "Loan",
        primaryValue: "-$250,000.00",
        metadata: "Wells Fargo",
        sourceOfTruth: "ledger",
        status: {
          label: "Stale",
          variant: "warning",
        },
        clickable: true,
      },
    },
  ],
});
