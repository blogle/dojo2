import { readFileSync, writeFileSync } from "node:fs";
import path from "node:path";
import process from "node:process";

const [manifestPath, outputPath] = process.argv.slice(2);
const runDirectories = readFileSync(manifestPath, "utf8").trim().split("\n");

const values = {
  baselineGenerationMs: [],
  apiStartupMs: [],
  webStartupMs: [],
  resetMs: [],
  suiteMs: [],
};

for (const runDirectory of runDirectories) {
  const harness = JSON.parse(
    readFileSync(path.join(runDirectory, "harness.json"), "utf8"),
  );
  const run = JSON.parse(
    readFileSync(path.join(runDirectory, "cypress", "run.json"), "utf8"),
  );
  values.baselineGenerationMs.push(harness.baselineGenerationMs);
  values.apiStartupMs.push(harness.apiStartupMs);
  values.webStartupMs.push(harness.webStartupMs);
  values.suiteMs.push(run.totalDurationMs);
  values.resetMs.push(
    ...run.tests.map(
      (test) => (test.reset?.restore_ms ?? 0) + (test.reset?.reopen_ms ?? 0),
    ),
  );
}

function percentile(samples, fraction) {
  const sorted = [...samples].sort((left, right) => left - right);
  const index = Math.min(
    sorted.length - 1,
    Math.max(0, Math.ceil(sorted.length * fraction) - 1),
  );
  return sorted[index];
}

const summary = Object.fromEntries(
  Object.entries(values).map(([name, samples]) => [
    name,
    {
      samples,
      median: percentile(samples, 0.5),
      p95: percentile(samples, 0.95),
    },
  ]),
);

writeFileSync(outputPath, JSON.stringify({ runDirectories, summary }, null, 2));
console.log("\nE2E profile summary");
for (const [name, metrics] of Object.entries(summary)) {
  console.log(
    `  ${name}: median=${metrics.median.toFixed(2)}ms p95=${metrics.p95.toFixed(2)}ms`,
  );
}
console.log(`  profile: ${outputPath}`);
