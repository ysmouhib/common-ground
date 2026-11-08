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

async function executeLean(executable: string, source: string): Promise<{ code: number; output: string }> {
  const directory = await mkdtemp(path.join(tmpdir(), "common-ground-"));
  try {
    const file = path.join(directory, "Proof.lean");
    await writeFile(file, source, "utf8");
    return await new Promise((resolve, reject) => {
      const child = spawn(executable, [file], {
        cwd: directory,
        env: { PATH: process.env.PATH ?? "", HOME: directory },
        stdio: ["ignore", "pipe", "pipe"],
      });
      let output = "";
      const timer = setTimeout(() => {
        child.kill("SIGKILL");
        reject(new Error("Lean verification exceeded the 20-second limit."));
      }, 20_000);
      child.stdout.on("data", (chunk) => {
        if (output.length < 50_000) output += chunk.toString();
      });
      child.stderr.on("data", (chunk) => {
        if (output.length < 50_000) output += chunk.toString();
      });
      child.on("error", (error) => {
        clearTimeout(timer);
        reject(error);
      });
      child.on("close", (code) => {
        clearTimeout(timer);
        resolve({ code: code ?? 1, output: output.trim().replaceAll(directory, ".") });
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

  if (!executable) {
    await db.insert(verificationRuns).values({
      proofId,
      sourceHash: hash,
      outcome: "unavailable",
      output: "No Lean executable is available in this runtime. The existing build-time certificate was left unchanged.",
      toolchain: LEAN_TOOLCHAIN,
    });
    return {
      proofId,
      runtimeAvailable: false,
      accepted: false,
      expectedOutcome: false,
      output: "Live Lean runtime unavailable; the stored certificate was not changed.",
      hash,
    };
  }

  if (FORBIDDEN_CONSTRUCTS.test(source)) {
    throw new TRPCError({ code: "BAD_REQUEST", message: "The proof source contains a disallowed trust construct." });
  }

  const result = await executeLean(executable, source);
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
    accepted,
    expectedOutcome,
    output,
    hash,
    toolchain: LEAN_TOOLCHAIN,
  };
}
