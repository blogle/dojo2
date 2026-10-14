export function localCalendarDate(value = new Date()): string {
  const year = String(value.getFullYear());
  const month = String(value.getMonth() + 1).padStart(2, "0");
  const day = String(value.getDate()).padStart(2, "0");
  return `${year}-${month}-${day}`;
}

export function localCalendarDateAsTimestamp(value: string): string {
  const localNoon = new Date(`${value}T12:00:00`);
  if (Number.isNaN(localNoon.getTime())) {
    throw new RangeError("Source-as-of date must be a valid calendar date.");
  }

  // Date fields are calendar dates; encode local noon with its offset as an instant.
  const offsetMinutes = localNoon.getTimezoneOffset();
  const offsetHours = String(Math.floor(Math.abs(offsetMinutes) / 60)).padStart(
    2,
    "0",
  );
  const offsetRemainder = String(Math.abs(offsetMinutes) % 60).padStart(2, "0");
  const offsetSign = offsetMinutes > 0 ? "-" : "+";
  return `${value}T12:00:00${offsetSign}${offsetHours}:${offsetRemainder}`;
}
