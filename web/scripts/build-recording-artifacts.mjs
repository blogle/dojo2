/** Build manifests and per-flow storyboards for a completed recording run. */

import { existsSync, readdirSync, readFileSync, writeFileSync } from "node:fs";
import { execFileSync } from "node:child_process";
import { createHash } from "node:crypto";
import path from "node:path";
import process from "node:process";

const recordingDir = process.argv[2];
if (!recordingDir) {
  console.error(
    "Usage: build-recording-artifacts.mjs <recording-dir> [command]",
  );
  process.exit(1);
}
const generationCommand = process.argv[3] || "web/scripts/run-e2e.sh --record";

function walkForExt(dir, ext, results = []) {
  if (!existsSync(dir)) return results;
  for (const entry of readdirSync(dir, { withFileTypes: true })) {
    const full = path.join(dir, entry.name);
    if (entry.isDirectory()) walkForExt(full, ext, results);
    else if (entry.name.endsWith(ext)) results.push(full);
  }
  return results;
}

function sha256File(filePath) {
  return createHash("sha256").update(readFileSync(filePath)).digest("hex");
}

function gitCommitSha() {
  try {
    return execFileSync("git", ["rev-parse", "--short", "HEAD"], {
      encoding: "utf8",
      stdio: ["ignore", "pipe", "ignore"],
    }).trim();
  } catch {
    return "unknown";
  }
}

function hasFfmpeg() {
  try {
    execFileSync("ffmpeg", ["-version"], { stdio: "ignore" });
    return true;
  } catch {
    return false;
  }
}

function flowFromVideo(videoPath) {
  return path
    .basename(videoPath, ".mp4")
    .replace(/\s*\(attempt \d+\)$/i, "")
    .replace(/\.cy\.ts$/i, "");
}

function flowFromSpec(spec) {
  return path.basename(spec).replace(/\.cy\.ts$/i, "");
}

const videos = walkForExt(recordingDir, ".mp4");
const checkpointPngs = walkForExt(
  path.join(recordingDir, "screenshots"),
  ".png",
);
const pngByBasename = new Map(
  checkpointPngs.map((png) => [path.basename(png), png]),
);
const checkpointsPath = path.join(recordingDir, "checkpoints.jsonl");
const checkpoints = existsSync(checkpointsPath)
  ? readFileSync(checkpointsPath, "utf8")
      .split("\n")
      .filter(Boolean)
      .flatMap((line) => {
        try {
          return [JSON.parse(line)];
        } catch {
          return [];
        }
      })
  : [];

if (videos.length === 0) {
  console.error(
    `ERROR: Recording completed without a Cypress video in ${recordingDir}. ` +
      "No recording spec may have been selected; recording specs are supplied by DOJO-22.",
  );
  process.exit(1);
}

const commitSha = gitCommitSha();
const ffmpegAvailable = hasFfmpeg();
if (!ffmpegAvailable) {
  console.error("ERROR: ffmpeg is required to generate recording storyboards.");
  process.exit(1);
}
const storyboards = [];
const manifests = [];

for (const video of videos) {
  const flow = flowFromVideo(video);
  const flowCheckpoints = checkpoints.filter(
    (checkpoint) => checkpoint.spec && flowFromSpec(checkpoint.spec) === flow,
  );
  const images = flowCheckpoints.map((checkpoint) => {
    const basename = path.basename(checkpoint.screenshotPath || "");
    return pngByBasename.get(basename);
  });
  const missing = flowCheckpoints.filter((_, index) => !images[index]);

  if (missing.length > 0) {
    console.error(
      `ERROR: Passed recording for flow "${flow}" is missing ${missing.length} ` +
        "checkpoint screenshot(s): " +
        missing.map((checkpoint) => checkpoint.label).join(", "),
    );
    process.exit(1);
  }
  if (flowCheckpoints.length === 0) {
    console.error(
      `ERROR: Passed recording for flow "${flow}" has no checkpoint metadata. ` +
        "DOJO-21 requires checkpoint screenshots for every recording.",
    );
    process.exit(1);
  }

  const manifestPath = path.join(recordingDir, `${flow}.manifest.txt`);
  const manifest = [
    "=== Recording Manifest ===",
    `Flow: ${flow}`,
    `Source spec: ${flowCheckpoints[0].spec}`,
    `Commit: ${commitSha}`,
    `Command: ${generationCommand}`,
    `Video: ${video}`,
    `Video SHA256: ${sha256File(video)}`,
    "Duration: unknown (not probed; ffmpeg is the only recording dependency)",
    "",
    "Checkpoints:",
    ...flowCheckpoints.map(
      (checkpoint, index) =>
        `  [${index + 1}] ${checkpoint.label}: ${images[index]}`,
    ),
    "",
  ];
  writeFileSync(manifestPath, `${manifest.join("\n")}\n`);
  manifests.push(manifestPath);

  const storyboardPath = path.join(recordingDir, `${flow}.storyboard.png`);
  const thumbW = 400;
  const thumbH = 225;
  const cols = Math.ceil(Math.sqrt(images.length));
  const layout = images
    .map(
      (_, index) =>
        `${(index % cols) * thumbW}_${Math.floor(index / cols) * thumbH}`,
    )
    .join("|");
  const filters = images
    .map(
      (_, index) =>
        `[${index}:v]scale=${thumbW}:${thumbH}:force_original_aspect_ratio=decrease,` +
        `pad=${thumbW}:${thumbH}:(ow-iw)/2:(oh-ih)/2:color=0x222222,` +
        `drawtext=text='${index + 1}':fontsize=22:x=8:y=8:` +
        "fontcolor=white:shadowcolor=black:shadowx=2:shadowy=2" +
        `[v${index}]`,
    )
    .join(";");
  const stack = images.map((_, index) => `[v${index}]`).join("");
  try {
    execFileSync(
      "ffmpeg",
      [
        "-y",
        ...images.flatMap((image) => ["-i", image]),
        "-filter_complex",
        `${filters};${stack}xstack=inputs=${images.length}:layout=${layout}`,
        "-frames:v",
        "1",
        storyboardPath,
      ],
      { stdio: "ignore" },
    );
  } catch (error) {
    console.error(
      `ERROR: ffmpeg failed to generate ${storyboardPath}: ${error.message}`,
    );
    process.exit(1);
  }
  storyboards.push(storyboardPath);
}

console.log(`Recording directory: ${recordingDir}`);
console.log(`Manifests (${manifests.length}):\n  ${manifests.join("\n  ")}`);
console.log(
  `Storyboards (${storyboards.length}):\n  ${storyboards.join("\n  ")}`,
);
