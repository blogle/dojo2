import { describe, expect, it } from "vitest";

import {
  localCalendarDate,
  localCalendarDateAsTimestamp,
} from "../src/dojo/utils/date";

describe("localCalendarDateAsTimestamp", () => {
  it("keeps the selected calendar day and includes the local timezone offset", () => {
    const selectedDate = "2026-06-30";
    const timestamp = localCalendarDateAsTimestamp(selectedDate);
    const localInstant = new Date(timestamp);

    expect(timestamp).to.match(/T12:00:00[+-]\d{2}:\d{2}$/);
    expect([
      localInstant.getFullYear(),
      String(localInstant.getMonth() + 1).padStart(2, "0"),
      String(localInstant.getDate()).padStart(2, "0"),
      localInstant.getHours(),
    ]).to.deep.equal([2026, "06", "30", 12]);
  });

  it("formats today's date in the user's local calendar", () => {
    const today = new Date();
    expect(localCalendarDate(today)).to.equal(
      `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, "0")}-${String(today.getDate()).padStart(2, "0")}`,
    );
  });
});
