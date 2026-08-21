import { readFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";

const [runDir, budgetPath] = process.argv.slice(2);
const harness = JSON.parse(
  readFileSync(path.join(runDir, "harness.json"), "utf8"),
);
const run = JSON.parse(
  readFileSync(path.join(runDir, "cypress", "run.json"), "utf8"),
);
const budget = JSON.parse(readFileSync(budgetPath, "utf8"));
const actual = {
  baselineGenerationMs: harness.baselineGenerationMs,
  apiStartupMs: harness.apiStartupMs,
  webStartupMs: harness.webStartupMs,
  resetMs: Math.max(
    0,
    ...run.tests.map(
      (test) => (test.reset?.restore_ms ?? 0) + (test.reset?.reopen_ms ?? 0),
    ),
  ),
  testMs: Math.max(0, ...run.tests.map((test) => test.durationMs ?? 0)),
  suiteMs: run.totalDurationMs,
  apiRequests: run.tests.reduce((sum, test) => sum + test.requestCount, 0),
  failedApiRequests: run.tests.reduce(
    (sum, test) => sum + test.failedRequestCount,
    0,
  ),
};

const failures = Object.entries(budget.ceilings).flatMap(([name, ceiling]) =>
  actual[name] > ceiling
    ? [`${name}: ${actual[name]} exceeded ${ceiling}`]
    : [],
);
const actualTests = run.tests.map((test) => test.title).sort();
const expectedTests = [...budget.expectedTests].sort();
if (
  run.totalTests !== expectedTests.length ||
  run.totalPassed !== expectedTests.length ||
  run.totalFailed !== 0 ||
  run.tests.some((test) => test.state !== "passed")
) {
  failures.push(
    `suite result differed: total=${run.totalTests}, passed=${run.totalPassed}, failed=${run.totalFailed}`,
  );
}
if (JSON.stringify(actualTests) !== JSON.stringify(expectedTests)) {
  failures.push(
    `scenario set differed: expected ${expectedTests.length}, recorded ${actualTests.length}`,
  );
}

if (failures.length > 0) {
  console.error("\nE2E performance budget failed");
  for (const failure of failures) console.error(`  ${failure}`);
  process.exit(1);
}

console.log("\nE2E performance budget passed");
for (const [name, ceiling] of Object.entries(budget.ceilings)) {
  console.log(`  ${name}: ${actual[name]} / ${ceiling}`);
}
