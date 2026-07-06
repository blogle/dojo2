import { defineFixtures } from "@/dojo/components/fixtures";

import StatusStepList from "./StatusStepList.vue";

type StatusStepListProps = InstanceType<typeof StatusStepList>["$props"];

export default defineFixtures<StatusStepListProps>({
  component: StatusStepList,
  title: "Status Step List",
  description:
    "Ordered list of process steps with status icons and badges for migration or import flows.",
  scenarios: [
    {
      name: "in-progress",
      props: {
        steps: [
          {
            title: "Reading Google Sheet",
            description: "Connected and read 4,032 rows.",
            status: "complete" as const,
          },
          {
            title: "Importing records",
            description: "Importing budgets, actuals, and related data.",
            status: "in-progress" as const,
          },
          {
            title: "Validating records",
            description:
              "Checking data integrity and preparing your workspace.",
            status: "pending" as const,
          },
        ],
      },
    },
    {
      name: "all complete",
      props: {
        steps: [
          {
            title: "Reading Google Sheet",
            description: "Connected and read 4,032 rows.",
            status: "complete" as const,
          },
          {
            title: "Importing records",
            description: "Importing budgets, actuals, and related data.",
            status: "complete" as const,
          },
          {
            title: "Validating records",
            description:
              "Checking data integrity and preparing your workspace.",
            status: "complete" as const,
          },
        ],
      },
    },
    {
      name: "all pending",
      props: {
        steps: [
          {
            title: "Step one",
            description: "Waiting to start.",
            status: "pending" as const,
          },
          {
            title: "Step two",
            description: "Waiting for step one.",
            status: "pending" as const,
          },
        ],
      },
    },
  ],
});
