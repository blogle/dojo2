import { readFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";

const runDir = process.argv[2];
const harness = JSON.parse(
  readFileSync(path.join(runDir, "harness.json"), "utf8"),
);
const run = JSON.parse(
  readFileSync(path.join(runDir, "cypress", "run.json"), "utf8"),
);
const resetDurations = run.tests.map(
  (test) => (test.reset?.restore_ms ?? 0) + (test.reset?.reopen_ms ?? 0),
);
const slowestTest = run.tests.reduce(
  (slowest, test) =>
    (test.durationMs ?? 0) > (slowest?.durationMs ?? 0) ? test : slowest,
  null,
);

console.log("\nE2E performance summary");
console.log(`  baseline generation: ${harness.baselineGenerationMs}ms`);
console.log(
  `  baseline size: ${(harness.baselineBytes / 1024 / 1024).toFixed(2)}MiB`,
);
console.log(`  API startup: ${harness.apiStartupMs}ms`);
console.log(`  web startup: ${harness.webStartupMs}ms`);
console.log(`  slowest reset: ${Math.max(0, ...resetDurations).toFixed(2)}ms`);
console.log(
  `  slowest test: ${slowestTest?.title ?? "n/a"} (${slowestTest?.durationMs ?? 0}ms)`,
);
console.log(
  `  API requests: ${run.tests.reduce((sum, test) => sum + test.requestCount, 0)}`,
);
console.log(`  suite duration: ${run.totalDurationMs}ms`);
console.log(`  artifacts: ${runDir}`);
