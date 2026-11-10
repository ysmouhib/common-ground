import { chmodSync, mkdtempSync, rmSync, writeFileSync } from "node:fs";
import { tmpdir } from "node:os";
import path from "node:path";
import { afterAll, describe, expect, it } from "vitest";
import { executeLean, leanTimeoutMs } from "./proofVerifier";

// Stand-ins for the Lean binary: small shell scripts that behave like the cases the
// verifier has to tell apart. The real binary is exercised by the end-to-end checks.
const directory = mkdtempSync(path.join(tmpdir(), "fake-lean-"));
function fake(name: string, script: string): string {
  const file = path.join(directory, name);
  writeFileSync(file, `#!/bin/sh\n${script}\n`);
  chmodSync(file, 0o755);
  return file;
}
afterAll(() => rmSync(directory, { recursive: true, force: true }));

describe("running Lean", () => {
  it("reports the exit code and the diagnostics, without the temporary path", async () => {
    const accepted = await executeLean(fake("accepts", 'echo "checked $1"'), "theorem t : True := trivial");
    expect(accepted).toEqual({ kind: "finished", code: 0, output: "checked ./Proof.lean" });
    const rejected = await executeLean(fake("rejects", 'echo "error: unsolved goals" >&2; exit 1'), "x");
    expect(rejected).toEqual({ kind: "finished", code: 1, output: "error: unsolved goals" });
  });

  it("gives the source to the program as a file", async () => {
    const run = await executeLean(fake("prints", 'cat "$1"'), "theorem t : True := trivial");
    expect(run).toEqual({ kind: "finished", code: 0, output: "theorem t : True := trivial" });
  });

  it("does not pass the server's environment to the program", async () => {
    process.env.FAKE_LEAN_SECRET = "must-not-leak";
    try {
      const run = await executeLean(fake("env", "env"), "x");
      expect(run.kind).toBe("finished");
      expect(run.kind === "finished" && run.output).not.toContain("must-not-leak");
    } finally {
      delete process.env.FAKE_LEAN_SECRET;
    }
  });

  it("a run that does not finish is not a verdict", async () => {
    const started = Date.now();
    // exec: the shell is replaced by the program, as with the real binary, so the kill reaches it.
    const run = await executeLean(fake("hangs", "exec sleep 30"), "x", 300);
    expect(run).toEqual({ kind: "timed_out", afterMs: 300 });
    expect(Date.now() - started).toBeLessThan(5_000);
  });

  it("a program that cannot be started is not a verdict either", async () => {
    const run = await executeLean(path.join(directory, "missing"), "x");
    expect(run.kind).toBe("not_started");
  });

  it("the time limit is configurable within bounds", () => {
    expect(leanTimeoutMs({})).toBe(60_000);
    expect(leanTimeoutMs({ LEAN_TIMEOUT_MS: "120000" })).toBe(120_000);
    expect(leanTimeoutMs({ LEAN_TIMEOUT_MS: "1" })).toBe(5_000);
    expect(leanTimeoutMs({ LEAN_TIMEOUT_MS: "99999999" })).toBe(300_000);
    expect(leanTimeoutMs({ LEAN_TIMEOUT_MS: "soon" })).toBe(60_000);
  });
});
