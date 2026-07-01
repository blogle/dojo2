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
