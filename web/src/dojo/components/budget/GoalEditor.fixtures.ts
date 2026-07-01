import { defineFixtures } from "@/dojo/components/fixtures";

import GoalEditor from "./GoalEditor.vue";

type GoalEditorProps = {
  goalType: string | null;
  goalAmountMinor: number | null;
  goalFrequency: string | null;
  goalDueDate: string | null;
  monthlyFundingMinor: number;
  disabled?: boolean;
};

export default defineFixtures<GoalEditorProps>({
  component: GoalEditor,
  title: "Goal Editor",
  description:
    "Goal type selector with conditional fields for one-time, recurring, and discretionary goals.",
  scenarios: [
    {
      name: "no goal type",
      props: {
        goalType: null,
        goalAmountMinor: null,
        goalFrequency: null,
        goalDueDate: null,
        monthlyFundingMinor: 0,
      },
    },
    {
      name: "one-time goal",
      props: {
        goalType: "ONE_TIME",
        goalAmountMinor: 50000,
        goalFrequency: null,
        goalDueDate: "2026-12-01",
        monthlyFundingMinor: 10000,
      },
    },
    {
      name: "recurring goal",
      props: {
        goalType: "RECURRING",
        goalAmountMinor: 15000,
        goalFrequency: "MONTHLY",
        goalDueDate: "2026-07-01",
        monthlyFundingMinor: 15000,
      },
    },
    {
      name: "discretionary goal",
      props: {
        goalType: "DISCRETIONARY",
        goalAmountMinor: 20000,
        goalFrequency: null,
        goalDueDate: null,
        monthlyFundingMinor: 20000,
      },
    },
    {
      name: "disabled",
      props: {
        goalType: "RECURRING",
        goalAmountMinor: 15000,
        goalFrequency: "MONTHLY",
        goalDueDate: "2026-07-01",
        monthlyFundingMinor: 15000,
        disabled: true,
      },
    },
  ],
});
