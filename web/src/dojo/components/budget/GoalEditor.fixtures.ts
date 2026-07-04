import { defineFixtures } from "@/dojo/components/fixtures";

import GoalEditor from "./GoalEditor.vue";

type GoalEditorProps = InstanceType<typeof GoalEditor>["$props"];

export default defineFixtures<GoalEditorProps>({
  component: GoalEditor,
  title: "Goal Editor",
  description: "Editor for setting goal type, amount, frequency, and due date.",
  scenarios: [
    {
      name: "default",
      props: {
        goalType: null,
        goalAmountMinor: null,
        goalFrequency: null,
        goalDueDate: null,
        monthlyFundingMinor: 0,
      },
    },
    {
      name: "recurring",
      props: {
        goalType: "RECURRING",
        goalAmountMinor: 15000,
        goalFrequency: "MONTHLY",
        goalDueDate: "2026-07-01",
        monthlyFundingMinor: 15000,
      },
    },
    {
      name: "one-time",
      props: {
        goalType: "ONE_TIME",
        goalAmountMinor: 50000,
        goalFrequency: null,
        goalDueDate: "2026-12-01",
        monthlyFundingMinor: 10000,
      },
    },
    {
      name: "discretionary",
      props: {
        goalType: "DISCRETIONARY",
        goalAmountMinor: 20000,
        goalFrequency: null,
        goalDueDate: null,
        monthlyFundingMinor: 20000,
      },
    },
  ],
});
