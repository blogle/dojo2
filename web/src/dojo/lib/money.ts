export function formatMoneyMinor(amountMinor: number): string {
  const sign = amountMinor < 0 ? "-" : "";
  const absolute = Math.abs(amountMinor);
  const dollars = Math.floor(absolute / 100);
  const cents = absolute % 100;
  return `${sign}$${dollars.toLocaleString()}.${cents.toString().padStart(2, "0")}`;
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
