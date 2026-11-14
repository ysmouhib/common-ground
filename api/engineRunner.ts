import { spawn } from "node:child_process";

import { existsSync } from "node:fs";

import { mkdtemp, readFile, rm, writeFile } from "node:fs/promises";

import { tmpdir } from "node:os";

import path from "node:path";

import { parseCampReport, parseEngineJson, type CampReport } from "@contracts/engineReport";

import { parseCrosscampReport, type CrosscampReport } from "@contracts/crosscampReport";

import { parseExtractRun, type ExtractRun } from "@contracts/extractRun";

import { Gate } from "./lib/security";

import { leanExecutable } from "./proofVerifier";

/** One engine run at a time: each starts a Python process, and a second request is refused, not queued. */
export const engineGate = new Gate(1);

/** How long one engine run may take. */
export function engineTimeoutMs(env: Record<string, string | undefined> = process.env): number {
  const requested = Number.parseInt(env.ENGINE_TIMEOUT_MS ?? "", 10);
  return Number.isFinite(requested) ? Math.min(600_000, Math.max(5_000, requested)) : 120_000;
}

export function pythonExecutable(env: Record<string, string | undefined> = process.env): string {
  return env.ENGINE_PYTHON ?? env.PYTHON_BIN ?? (process.platform === "win32" ? "python" : "python3");
}

/** The engine checkout the bridge runs: ENGINE_DIR, or ./engine next to the app. */
export function engineDir(env: Record<string, string | undefined> = process.env): string | undefined {
  const candidates = [env.ENGINE_DIR, path.resolve(process.cwd(), "engine")].filter(
    (candidate): candidate is string => Boolean(candidate),
  );
  return candidates.find((dir) => existsSync(path.join(dir, "commonground", "__main__.py")));
}

export type EngineRun =
  | { kind: "finished"; code: number; output: string }
  | { kind: "timed_out"; afterMs: number }
  | { kind: "not_started"; reason: string };

/**
 * The only server variables the engine child may see. Python locates its own
 * site-packages through these (on Windows APPDATA, not HOME, holds the user
 * site-packages), so they are passed through by name; everything else — API keys
 * above all — stays on the server.
 */
const CHILD_ENV_PASSTHROUGH = [
  "PATH",
  "HOME",
  "APPDATA",
  "LOCALAPPDATA",
  "SYSTEMROOT",
  "SYSTEMDRIVE",
  "TEMP",
  "TMP",
  "LEAN_BIN",
  "PYTHONPATH",
  "PYTHONHOME",
] as const;

export function childEnvironment(env: Record<string, string | undefined>, fallbackHome: string): NodeJS.ProcessEnv {
  const out: NodeJS.ProcessEnv = {};
  for (const key of CHILD_ENV_PASSTHROUGH) {
    const value = env[key];
    if (value !== undefined) out[key] = value;
  }
  if (out.PATH === undefined) out.PATH = "";
  if (out.HOME === undefined && process.platform !== "win32") out.HOME = fallbackHome;
  return out;
}

/**
 * Run `python -m commonground …` once. A run that does not finish, or a binary that
 * cannot be started, is reported as such: neither is a verdict about the record.
 * The child gets only the environment it is given — never the server's.
 */
export async function executeEngine(
  executable: string,
  args: string[],
  opts: { cwd: string; timeoutMs?: number; env?: NodeJS.ProcessEnv },
): Promise<EngineRun> {
  const timeoutMs = opts.timeoutMs ?? engineTimeoutMs();
  return await new Promise<EngineRun>((resolve) => {
    const child = spawn(executable, args, {
      cwd: opts.cwd,
      env: opts.env ?? { PATH: process.env.PATH ?? "" },
      stdio: ["ignore", "pipe", "pipe"],
    });
    let output = "";
    let timedOut = false;
    const timer = setTimeout(() => {
      timedOut = true;
      child.kill("SIGKILL");
    }, timeoutMs);
    child.stdout.on("data", (chunk) => {
      if (output.length < 50_000) output += chunk.toString();
    });
    child.stderr.on("data", (chunk) => {
      if (output.length < 50_000) output += chunk.toString();
    });
    child.on("error", (error) => {
      clearTimeout(timer);
      resolve({ kind: "not_started", reason: error.message });
    });
    child.on("close", (code) => {
      clearTimeout(timer);
      if (timedOut) resolve({ kind: "timed_out", afterMs: timeoutMs });
      else resolve({ kind: "finished", code: code ?? 1, output: output.trim() });
    });
  });
}

export type CampRun =
  | { kind: "report"; report: CampReport }
  | { kind: "no_verdict"; reason: string }
  | { kind: "invalid_input"; message: string };

export interface CampRunInput {
  record: unknown;
  candidates: unknown;
  plausibilities?: unknown;
  lam: number;
  maxChecks: number;
  timeoutMs: number;
  lean: boolean;
}

/**
 * Spawn `python -m commonground camp …` in a temp dir and parse out/report.json.
 * A missing runtime, a timeout and an unreadable report are no_verdict answers —
 * an outage is never scored as a wrong answer. Exit code 2 means the engine
 * rejected the input (validation), reported as invalid_input, not as a verdict.
 */
export async function runCampReport(
  input: CampRunInput,
  env: Record<string, string | undefined> = process.env,
): Promise<CampRun> {
  const dir = engineDir(env);
  if (!dir) {
    return {
      kind: "no_verdict",
      reason: "The engine is not installed in this runtime (no engine/ directory), so no report was produced.",
    };
  }
  if (input.lean && !leanExecutable()) {
    return {
      kind: "no_verdict",
      reason:
        "Lean is not available in this runtime, so no kernel-checked report was produced; run again without lean for solver-checked badges.",
    };
  }
  const work = await mkdtemp(path.join(tmpdir(), "common-ground-camp-"));
  try {
    const recordPath = path.join(work, "record.json");
    const candidatesPath = path.join(work, "candidates.json");
    const plausibilitiesPath = path.join(work, "plausibilities.json");
    const out = path.join(work, "out");
    await writeFile(recordPath, JSON.stringify(input.record), "utf8");
    await writeFile(candidatesPath, JSON.stringify(input.candidates), "utf8");
    if (input.plausibilities !== undefined) {
      await writeFile(plausibilitiesPath, JSON.stringify(input.plausibilities), "utf8");
    }
    const args = [
      "-X",
      "utf8",
      "-m",
      "commonground",
      "--timeout-ms",
      String(input.timeoutMs),
      "camp",
      recordPath,
      "--candidates",
      candidatesPath,
      "--lam",
      String(input.lam),
      "--max-checks",
      String(input.maxChecks),
      "--out",
      out,
    ];
    if (input.plausibilities !== undefined) args.push("--plausibilities", plausibilitiesPath);
    if (input.lean) args.push("--lean");
    const run = await executeEngine(pythonExecutable(env), args, {
      cwd: dir,
      timeoutMs: engineTimeoutMs(env),
      env: childEnvironment(env, work),
    });
    if (run.kind === "not_started") {
      return { kind: "no_verdict", reason: `The engine process could not be started (${run.reason}). No report was produced.` };
    }
    if (run.kind === "timed_out") {
      const seconds = Math.round(run.afterMs / 1000);
      return { kind: "no_verdict", reason: `The engine did not finish within ${seconds} s, so there is no report.` };
    }
    const output = run.output.replaceAll(work, ".");
    if (run.code !== 0) {
      if (run.code === 2) {
        return { kind: "invalid_input", message: output.slice(0, 500) || "the engine rejected the input" };
      }
      return { kind: "no_verdict", reason: `The engine exited with code ${run.code}: ${output.slice(0, 300) || "no output"}` };
    }
    let raw: unknown;
    try {
      raw = parseEngineJson(await readFile(path.join(out, "report.json"), "utf8"));
    } catch {
      return {
        kind: "no_verdict",
        reason: `The engine finished but produced no readable report.json. Engine output: ${output.slice(0, 300) || "(none)"}`,
      };
    }
    try {
      return { kind: "report", report: parseCampReport(raw) };
    } catch {
      return { kind: "no_verdict", reason: "The engine's report did not match the API contract, so it was not shown." };
    }
  } finally {
    await rm(work, { recursive: true, force: true });
  }
}

export type CrosscampRun =
  | { kind: "report"; report: CrosscampReport; camps: Record<string, CampReport> }
  | { kind: "no_verdict"; reason: string }
  | { kind: "invalid_input"; message: string };

export interface CrosscampRunInput {
  records: unknown[];
  candidates: unknown[];
  plausibilities?: unknown;
  lam: number;
  maxChecks: number;
  timeoutMs: number;
  lean: boolean;
}

/**
 * Spawn `python -m commonground crosscamp …` in a temp dir and parse
 * out/crosscamp.json plus each out/<camp>/report.json. Same honesty rules as
 * runCampReport; the per-camp reports go through the same whitelist, so no
 * abstention reaches the API from either file.
 */
export async function runCrosscamp(
  input: CrosscampRunInput,
  env: Record<string, string | undefined> = process.env,
): Promise<CrosscampRun> {
  const dir = engineDir(env);
  if (!dir) {
    return {
      kind: "no_verdict",
      reason: "The engine is not installed in this runtime (no engine/ directory), so no report was produced.",
    };
  }
  if (input.lean && !leanExecutable()) {
    return {
      kind: "no_verdict",
      reason:
        "Lean is not available in this runtime, so no kernel-checked report was produced; run again without lean for solver-checked badges.",
    };
  }
  const work = await mkdtemp(path.join(tmpdir(), "common-ground-crosscamp-"));
  try {
    const recordPaths: string[] = [];
    const candidatesPaths: string[] = [];
    for (let i = 0; i < input.records.length; i += 1) {
      const recordPath = path.join(work, `record-${i}.json`);
      const candidatesPath = path.join(work, `candidates-${i}.json`);
      await writeFile(recordPath, JSON.stringify(input.records[i]), "utf8");
      await writeFile(candidatesPath, JSON.stringify(input.candidates[i]), "utf8");
      recordPaths.push(recordPath);
      candidatesPaths.push(candidatesPath);
    }
    const plausibilitiesPath = path.join(work, "plausibilities.json");
    if (input.plausibilities !== undefined) {
      await writeFile(plausibilitiesPath, JSON.stringify(input.plausibilities), "utf8");
    }
    const out = path.join(work, "out");
    // crosscamp defines its own --timeout-ms after the subcommand; the global one is shadowed.
    const args = [
      "-X",
      "utf8",
      "-m",
      "commonground",
      "crosscamp",
      ...recordPaths,
      "--candidates",
      ...candidatesPaths,
      "--lam",
      String(input.lam),
      "--timeout-ms",
      String(input.timeoutMs),
      "--max-checks",
      String(input.maxChecks),
      "--out",
      out,
    ];
    if (input.plausibilities !== undefined) args.push("--plausibilities", plausibilitiesPath);
    if (input.lean) args.push("--lean");
    const run = await executeEngine(pythonExecutable(env), args, {
      cwd: dir,
      timeoutMs: engineTimeoutMs(env),
      env: childEnvironment(env, work),
    });
    if (run.kind === "not_started") {
      return { kind: "no_verdict", reason: `The engine process could not be started (${run.reason}). No report was produced.` };
    }
    if (run.kind === "timed_out") {
      const seconds = Math.round(run.afterMs / 1000);
      return { kind: "no_verdict", reason: `The engine did not finish within ${seconds} s, so there is no report.` };
    }
    const output = run.output.replaceAll(work, ".");
    if (run.code !== 0) {
      if (run.code === 2) {
        return { kind: "invalid_input", message: output.slice(0, 500) || "the engine rejected the input" };
      }
      return { kind: "no_verdict", reason: `The engine exited with code ${run.code}: ${output.slice(0, 300) || "no output"}` };
    }
    let raw: unknown;
    try {
      raw = parseEngineJson(await readFile(path.join(out, "crosscamp.json"), "utf8"));
    } catch {
      return {
        kind: "no_verdict",
        reason: `The engine finished but produced no readable crosscamp.json. Engine output: ${output.slice(0, 300) || "(none)"}`,
      };
    }
    let report: CrosscampReport;
    try {
      report = parseCrosscampReport(raw);
    } catch {
      return { kind: "no_verdict", reason: "The engine's cross-camp report did not match the API contract, so it was not shown." };
    }
    const camps: Record<string, CampReport> = {};
    for (const camp of report.camps) {
      try {
        camps[camp] = parseCampReport(parseEngineJson(await readFile(path.join(out, camp, "report.json"), "utf8")));
      } catch {
        return { kind: "no_verdict", reason: `The report for camp ${camp} was unreadable or off-contract, so the cross-camp result was not shown.` };
      }
    }
    return { kind: "report", report, camps };
  } finally {
    await rm(work, { recursive: true, force: true });
  }
}

export type ExtractBridgeRun =
  | { kind: "run"; run: ExtractRun }
  | { kind: "no_verdict"; reason: string }
  | { kind: "invalid_input"; message: string };

export interface ExtractRunInput {
  documents: { id: string; text: string }[];
  baseUrl: string;
  model: string;
  maxTokens: number;
  noJsonMode: boolean;
  noTemperature: boolean;
}

/**
 * Spawn `python -m commonground extract …` in a temp dir holding the documents
 * (PYTHONPATH points at the engine). The API key never comes from the client:
 * the server's LLM_API_KEY is passed to the child and nowhere else. Engine exit
 * 3 is a provider outage — the run stopped, nothing was scored — and answers
 * no_verdict like a timeout does.
 */
export async function runExtract(
  input: ExtractRunInput,
  env: Record<string, string | undefined> = process.env,
): Promise<ExtractBridgeRun> {
  const dir = engineDir(env);
  if (!dir) {
    return {
      kind: "no_verdict",
      reason: "The engine is not installed in this runtime (no engine/ directory), so extraction cannot run.",
    };
  }
  const apiKey = env.LLM_API_KEY;
  if (!apiKey) {
    return {
      kind: "no_verdict",
      reason: "The server has no LLM_API_KEY, so extraction cannot run. This is a configuration gap, not a verdict on the texts.",
    };
  }
  const work = await mkdtemp(path.join(tmpdir(), "common-ground-extract-"));
  try {
    for (const doc of input.documents) {
      await writeFile(path.join(work, doc.id), doc.text, "utf8");
    }
    const out = path.join(work, "out");
    const args = [
      "-X",
      "utf8",
      "-m",
      "commonground",
      "extract",
      ...input.documents.map((doc) => doc.id),
      "--base-url",
      input.baseUrl,
      "--model",
      input.model,
      "--max-tokens",
      String(input.maxTokens),
      "--out",
      out,
    ];
    if (input.noJsonMode) args.push("--no-json-mode");
    if (input.noTemperature) args.push("--no-temperature");
    const childEnv = childEnvironment(env, work);
    childEnv.PYTHONPATH = dir;
    childEnv.LLM_API_KEY = apiKey;
    const run = await executeEngine(pythonExecutable(env), args, {
      cwd: work,
      timeoutMs: engineTimeoutMs(env),
      env: childEnv,
    });
    if (run.kind === "not_started") {
      return { kind: "no_verdict", reason: `The engine process could not be started (${run.reason}). No extraction was produced.` };
    }
    if (run.kind === "timed_out") {
      const seconds = Math.round(run.afterMs / 1000);
      return { kind: "no_verdict", reason: `The extraction did not finish within ${seconds} s, so there is no result.` };
    }
    const output = run.output.replaceAll(work, ".");
    if (run.code !== 0) {
      if (run.code === 2) {
        return { kind: "invalid_input", message: output.slice(0, 500) || "the engine rejected the input" };
      }
      // exit 3: the provider outage stopped the run; finished documents are kept, nothing is scored
      return {
        kind: "no_verdict",
        reason: `The extraction stopped without a result: ${output.slice(0, 300) || `engine exit code ${run.code}`}`,
      };
    }
    let summary: unknown;
    let rows: unknown[];
    try {
      summary = parseEngineJson(await readFile(path.join(out, "summary.json"), "utf8"));
      const log = await readFile(path.join(out, "runs.jsonl"), "utf8");
      rows = log
        .split("\n")
        .filter((line) => line.trim().length > 0)
        .map((line) => parseEngineJson(line));
    } catch {
      return {
        kind: "no_verdict",
        reason: `The engine finished but produced no readable extraction output. Engine output: ${output.slice(0, 300) || "(none)"}`,
      };
    }
    try {
      return { kind: "run", run: parseExtractRun(summary, rows) };
    } catch {
      return { kind: "no_verdict", reason: "The engine's extraction output did not match the API contract, so it was not shown." };
    }
  } finally {
    await rm(work, { recursive: true, force: true });
  }
}
