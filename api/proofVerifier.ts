import { createHash } from "node:crypto";
import { spawn } from "node:child_process";
import { existsSync } from "node:fs";
import { mkdtemp, rm, writeFile } from "node:fs/promises";
import { tmpdir } from "node:os";
import path from "node:path";
import { eq } from "drizzle-orm";
import { TRPCError } from "@trpc/server";
import { proofs, verificationRuns } from "@db/schema";
import { buildLeanSource, buildNegativeControlSource, LEAN_TOOLCHAIN } from "@contracts/lean";
import { getDb } from "./queries/connection";

const FORBIDDEN_CONSTRUCTS = /\b(sorry|admit|axiom|unsafe|native_decide|extern|implemented_by)\b/;

function leanExecutable(): string | undefined {
  const candidates = [
    process.env.LEAN_BIN,
    "/tmp/lean-runtime/lean-4.35.0-linux/bin/lean",
    path.resolve(process.cwd(), "dist/lean-runtime/bin/lean"),
    path.resolve(process.cwd(), "public/lean-runtime/bin/lean"),
  ].filter((candidate): candidate is string => Boolean(candidate));
  return candidates.find((candidate) => existsSync(candidate));
}

/** How long one Lean run may take. The first run after a cold start reads the whole toolchain from disk. */
export function leanTimeoutMs(env: Record<string, string | undefined> = process.env): number {
  const requested = Number.parseInt(env.LEAN_TIMEOUT_MS ?? "", 10);
  return Number.isFinite(requested) ? Math.min(300_000, Math.max(5_000, requested)) : 60_000;
}

export type LeanRun =
  | { kind: "finished"; code: number; output: string }
  | { kind: "timed_out"; afterMs: number }
  | { kind: "not_started"; reason: string };

/**
 * Run Lean on one source file. A run that does not finish, or a binary that cannot
 * be started, is reported as such: neither is a verdict about the proof.
 */
export async function executeLean(executable: string, source: string, timeoutMs = leanTimeoutMs()): Promise<LeanRun> {
  const directory = await mkdtemp(path.join(tmpdir(), "common-ground-"));
  try {
    const file = path.join(directory, "Proof.lean");
    await writeFile(file, source, "utf8");
    return await new Promise<LeanRun>((resolve) => {
      const child = spawn(executable, [file], {
        cwd: directory,
        env: { PATH: process.env.PATH ?? "", HOME: directory },
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
        resolve({ kind: "not_started", reason: error.message.replaceAll(directory, ".") });
      });
      child.on("close", (code) => {
        clearTimeout(timer);
        if (timedOut) resolve({ kind: "timed_out", afterMs: timeoutMs });
        else resolve({ kind: "finished", code: code ?? 1, output: output.trim().replaceAll(directory, ".") });
      });
    });
  } finally {
    await rm(directory, { recursive: true, force: true });
  }
}

export async function verifyProof(proofId: string) {
  const db = getDb();
  const [proof] = await db.select().from(proofs).where(eq(proofs.id, proofId)).limit(1);
  if (!proof) throw new TRPCError({ code: "NOT_FOUND", message: "Proof not found." });

  const source = proof.isNegativeControl
    ? buildNegativeControlSource()
    : buildLeanSource(proof.theoremName);
  const hash = createHash("sha256").update(source).digest("hex");
  const executable = leanExecutable();

  // No verdict was reached: record why, change nothing about the stored certificate.
  const noVerdict = async (runtimeAvailable: boolean, timedOut: boolean, recorded: string, shown: string) => {
    await db.insert(verificationRuns).values({
      proofId,
      sourceHash: hash,
      outcome: "unavailable",
      output: recorded,
      toolchain: LEAN_TOOLCHAIN,
    });
    return { proofId, runtimeAvailable, timedOut, accepted: false, expectedOutcome: false, output: shown, hash, toolchain: LEAN_TOOLCHAIN };
  };

  if (!executable) {
    return noVerdict(
      false,
      false,
      "No Lean executable is available in this runtime. The existing build-time certificate was left unchanged.",
      "Live Lean runtime unavailable; the stored certificate was not changed.",
    );
  }

  if (FORBIDDEN_CONSTRUCTS.test(source)) {
    throw new TRPCError({ code: "BAD_REQUEST", message: "The proof source contains a disallowed trust construct." });
  }

  const result = await executeLean(executable, source);
  if (result.kind === "not_started") {
    return noVerdict(
      false,
      false,
      `The Lean executable could not be started (${result.reason}). The stored certificate was left unchanged.`,
      "Live Lean runtime unavailable: the Lean executable could not be started. The stored certificate was not changed.",
    );
  }
  if (result.kind === "timed_out") {
    const seconds = Math.round(result.afterMs / 1000);
    return noVerdict(
      true,
      true,
      `Lean did not finish within ${seconds} seconds, so there is no verdict. The stored certificate was left unchanged.`,
      `Lean did not finish within ${seconds} seconds, so there is no verdict; the stored certificate was not changed. The first run after a restart is the slowest: run it again.`,
    );
  }
  const accepted = result.code === 0 && !result.output.includes("sorryAx");
  const expectedOutcome = proof.isNegativeControl ? !accepted : accepted;
  const status = accepted ? ("verified" as const) : ("failed" as const);
  const output = result.output || (accepted ? "Lean accepted the file without diagnostics." : "Lean rejected the file.");

  await db
    .update(proofs)
    .set({
      status,
      verifierOutput: output,
      axiomReport: accepted && !proof.isNegativeControl ? output : null,
      proofHash: hash,
      toolchain: LEAN_TOOLCHAIN,
      verifiedAt: new Date(),
    })
    .where(eq(proofs.id, proofId));
  await db.insert(verificationRuns).values({
    proofId,
    sourceHash: hash,
    outcome: accepted ? "accepted" : "rejected",
    output,
    toolchain: LEAN_TOOLCHAIN,
  });

  return {
    proofId,
    runtimeAvailable: true,
    timedOut: false,
    accepted,
    expectedOutcome,
    output,
    hash,
    toolchain: LEAN_TOOLCHAIN,
  };
}
