import * as v from "valibot";

export const MoneyMinorSchema = v.pipe(v.number(), v.integer());

export const BudgetMonthSchema = v.pipe(
  v.string(),
  v.regex(/^\d{4}-(0[1-9]|1[0-2])$/, "Expected YYYY-MM format"),
);

export const GoalDateSchema = v.pipe(
  v.string(),
  v.regex(
    /^\d{4}-(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$/,
    "Expected YYYY-MM-DD format",
  ),
  v.check((value) => {
    const [year, month, day] = value.split("-").map(Number);
    const date = new Date(year, month - 1, day);
    return (
      date.getFullYear() === year &&
      date.getMonth() === month - 1 &&
      date.getDate() === day
    );
  }, "Invalid date"),
);

export type MoneyMinor = v.InferOutput<typeof MoneyMinorSchema>;
export type BudgetMonth = v.InferOutput<typeof BudgetMonthSchema>;
export type GoalDate = v.InferOutput<typeof GoalDateSchema>;
