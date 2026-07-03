import { describe, expect, it } from "vitest";
import * as v from "valibot";

import { formatCurrency, parseMoneyInput } from "../src/dojo/utils/currency";
import {
  BudgetMonthSchema,
  GoalDateSchema,
  MoneyMinorSchema,
} from "../src/dojo/lib/schemas";

describe("parseMoneyInput", () => {
  it("parses a simple decimal string", () => {
    expect(parseMoneyInput("12.50")).toBe(1250);
  });

  it("parses a whole number", () => {
    expect(parseMoneyInput("100")).toBe(10000);
  });

  it("parses zero", () => {
    expect(parseMoneyInput("0")).toBe(0);
  });

  it("parses negative amounts", () => {
    expect(parseMoneyInput("-25.99")).toBe(-2599);
  });

  it("strips dollar sign", () => {
    expect(parseMoneyInput("$42.00")).toBe(4200);
  });

  it("strips commas", () => {
    expect(parseMoneyInput("1,234.56")).toBe(123456);
  });

  it("strips dollar sign and commas", () => {
    expect(parseMoneyInput("$1,234.56")).toBe(123456);
  });

  it("returns null for empty string", () => {
    expect(parseMoneyInput("")).toBeNull();
  });

  it("returns null for whitespace only", () => {
    expect(parseMoneyInput("   ")).toBeNull();
  });

  it("returns null for non-numeric text", () => {
    expect(parseMoneyInput("abc")).toBeNull();
  });

  it("returns null for mixed text", () => {
    expect(parseMoneyInput("12abc")).toBeNull();
  });

  it("rounds to nearest cent", () => {
    expect(parseMoneyInput("10.005")).toBe(1001);
  });

  it("handles single decimal place", () => {
    expect(parseMoneyInput("5.5")).toBe(550);
  });

  it("trims leading and trailing whitespace", () => {
    expect(parseMoneyInput("  10.00  ")).toBe(1000);
  });
});

describe("formatCurrency", () => {
  it("formats positive amounts", () => {
    expect(formatCurrency(1250)).toBe("$12.50");
  });

  it("formats zero", () => {
    expect(formatCurrency(0)).toBe("$0.00");
  });

  it("formats negative amounts with minus sign", () => {
    expect(formatCurrency(-2599)).toBe("-$25.99");
  });

  it("formats large amounts with comma grouping", () => {
    expect(formatCurrency(12345600)).toBe("$123,456.00");
  });

  it("formats amounts less than a dollar", () => {
    expect(formatCurrency(5)).toBe("$0.05");
  });
});

describe("MoneyMinorSchema", () => {
  it("accepts valid integers", () => {
    expect(v.parse(MoneyMinorSchema, 0)).toBe(0);
    expect(v.parse(MoneyMinorSchema, 100)).toBe(100);
    expect(v.parse(MoneyMinorSchema, -500)).toBe(-500);
  });

  it("rejects non-integers", () => {
    expect(() => v.parse(MoneyMinorSchema, 10.5)).toThrow();
  });

  it("rejects NaN", () => {
    expect(() => v.parse(MoneyMinorSchema, NaN)).toThrow();
  });

  it("rejects Infinity", () => {
    expect(() => v.parse(MoneyMinorSchema, Infinity)).toThrow();
  });
});

describe("BudgetMonthSchema", () => {
  it("accepts valid YYYY-MM", () => {
    expect(v.parse(BudgetMonthSchema, "2026-01")).toBe("2026-01");
    expect(v.parse(BudgetMonthSchema, "2026-12")).toBe("2026-12");
  });

  it("rejects single-digit month", () => {
    expect(() => v.parse(BudgetMonthSchema, "2026-1")).toThrow();
  });

  it("rejects month 13", () => {
    expect(() => v.parse(BudgetMonthSchema, "2026-13")).toThrow();
  });

  it("rejects full date string", () => {
    expect(() => v.parse(BudgetMonthSchema, "2026-01-15")).toThrow();
  });

  it("rejects empty string", () => {
    expect(() => v.parse(BudgetMonthSchema, "")).toThrow();
  });

  it("rejects random text", () => {
    expect(() => v.parse(BudgetMonthSchema, "hello")).toThrow();
  });
});

describe("GoalDateSchema", () => {
  it("accepts valid dates", () => {
    expect(v.parse(GoalDateSchema, "2026-01-15")).toBe("2026-01-15");
    expect(v.parse(GoalDateSchema, "2026-12-31")).toBe("2026-12-31");
  });

  it("rejects Feb 30", () => {
    expect(() => v.parse(GoalDateSchema, "2026-02-30")).toThrow();
  });

  it("rejects Feb 29 in non-leap year", () => {
    expect(() => v.parse(GoalDateSchema, "2025-02-29")).toThrow();
  });

  it("accepts Feb 29 in leap year", () => {
    expect(v.parse(GoalDateSchema, "2024-02-29")).toBe("2024-02-29");
  });

  it("rejects month 13", () => {
    expect(() => v.parse(GoalDateSchema, "2026-13-01")).toThrow();
  });

  it("rejects day 32", () => {
    expect(() => v.parse(GoalDateSchema, "2026-01-32")).toThrow();
  });

  it("rejects YYYY-MM format", () => {
    expect(() => v.parse(GoalDateSchema, "2026-01")).toThrow();
  });

  it("rejects empty string", () => {
    expect(() => v.parse(GoalDateSchema, "")).toThrow();
  });
});
