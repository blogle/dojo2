export function formatCurrency(minor: number): string {
  const abs = Math.abs(minor) / 100;
  const formatted = abs.toLocaleString("en-US", {
    minimumFractionDigits: 2,
    maximumFractionDigits: 2,
  });
  return minor < 0 ? `-$${formatted}` : `$${formatted}`;
}

export function formatDelta(from: number, to: number): string {
  return `${formatCurrency(from)} \u2192 ${formatCurrency(to)}`;
}

export function formatMonth(month: string): string {
  const [year, monthNum] = month.split("-").map(Number);
  const date = new Date(year, monthNum - 1);
  return date.toLocaleDateString("en-US", { month: "long", year: "numeric" });
}

export function formatGoalType(type: string): string {
  const labels: Record<string, string> = {
    ONE_TIME: "One-time",
    RECURRING: "Recurring",
    DISCRETIONARY: "Discretionary",
  };
  return labels[type] ?? type;
}

export function parseMoneyInput(raw: string): number | null {
  const value = raw.trim();
  if (!value) {
    return null;
  }
  const normalized = value.replace(/[$,]/g, "");
  const amount = Number(normalized);
  if (Number.isNaN(amount)) {
    return null;
  }
  return Math.round(amount * 100);
}
