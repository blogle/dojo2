export const commonInstitutions = [
  "Ally Bank",
  "Bank of America",
  "Capital One",
  "Chase",
  "Charles Schwab",
  "Citi",
  "Fidelity",
  "Navy Federal Credit Union",
  "SoFi",
  "USAA",
  "Vanguard",
  "Wells Fargo",
] as const;

export function institutionSuggestions(
  existingInstitutions: Array<string | null | undefined>,
): string[] {
  return Array.from(
    new Set(
      [...existingInstitutions, ...commonInstitutions]
        .map((institution) => institution?.trim())
        .filter((institution): institution is string => Boolean(institution)),
    ),
  ).sort((left, right) => left.localeCompare(right));
}
