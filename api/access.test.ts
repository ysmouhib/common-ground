import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

vi.mock("./proofVerifier", () => ({
  verifyProof: vi.fn(async (proofId: string) => ({ proofId, accepted: true })),
}));
vi.mock("./queries/workspace", () => ({
  getWorkspace: vi.fn(async () => ({ statements: [], proofs: [] })),
}));

import { appRouter } from "./router";
import { accessFor } from "./lib/security";
import { verifyProof } from "./proofVerifier";

const TOKEN = "a-long-random-reviewer-token-0123456789";
let client = 0;

function caller(authorization?: string, key = `client-${(client += 1)}`) {
  const req = new Request("http://localhost/api/trpc/x", { headers: authorization ? { authorization } : {} });
  return appRouter.createCaller({ req, resHeaders: new Headers(), access: accessFor(req), clientKey: key });
}

const mutations = (api: ReturnType<typeof caller>) => [
  () => api.proof.verify({ proofId: "proof-advocate" }),
  () => api.proof.verifyAll(),
  () => api.workspace.setStatementStatus({ statementId: "A1", status: "disputed", note: "testing" }),
  () => api.ai.critiqueFormalization({ statementId: "A1" }),
];

describe("who may do what", () => {
  beforeEach(() => vi.mocked(verifyProof).mockClear());
  afterEach(() => {
    delete process.env.REVIEWER_TOKEN;
  });

  it("anyone can read", async () => {
    await expect(caller().ping()).resolves.toMatchObject({ ok: true });
    await expect(caller().workspace.get()).resolves.toMatchObject({ access: { reviewEnabled: false, isReviewer: false } });
  });

  it("with no token configured every mutation is refused, even with a token in the request", async () => {
    for (const authorization of [undefined, `Bearer ${TOKEN}`]) {
      for (const call of mutations(caller(authorization))) {
        await expect(call()).rejects.toMatchObject({ code: "FORBIDDEN" });
      }
    }
    expect(verifyProof).not.toHaveBeenCalled();
  });

  it("with a token configured, a missing or wrong token is refused before anything runs", async () => {
    process.env.REVIEWER_TOKEN = TOKEN;
    for (const authorization of [undefined, "Bearer wrong-token", `Bearer ${TOKEN}x`, TOKEN]) {
      for (const call of mutations(caller(authorization))) {
        await expect(call()).rejects.toMatchObject({ code: "UNAUTHORIZED" });
      }
    }
    expect(verifyProof).not.toHaveBeenCalled();
  });

  it("the right token reaches the handler and the workspace reports it", async () => {
    process.env.REVIEWER_TOKEN = TOKEN;
    const api = caller(`Bearer ${TOKEN}`);
    await expect(api.proof.verify({ proofId: "proof-advocate" })).resolves.toMatchObject({ accepted: true });
    await expect(api.proof.verifyAll()).resolves.toHaveLength(5);
    await expect(api.workspace.get()).resolves.toMatchObject({ access: { reviewEnabled: true, isReviewer: true } });
  });

  it("repeated wrong tokens lock a client out, even for the right token", async () => {
    process.env.REVIEWER_TOKEN = TOKEN;
    const key = "guessing-client";
    for (let i = 0; i < 10; i += 1) {
      await expect(caller(`Bearer guess-${i}`, key).proof.verifyAll()).rejects.toMatchObject({ code: "UNAUTHORIZED" });
    }
    await expect(caller(`Bearer ${TOKEN}`, key).proof.verifyAll()).rejects.toMatchObject({ code: "TOO_MANY_REQUESTS" });
    await expect(caller(`Bearer ${TOKEN}`, "another-client").proof.verifyAll()).resolves.toHaveLength(5);
  });

  it("only one Lean verification runs at a time", async () => {
    process.env.REVIEWER_TOKEN = TOKEN;
    let finish: () => void = () => {};
    vi.mocked(verifyProof).mockImplementationOnce(
      () => new Promise((resolve) => { finish = () => resolve({ proofId: "proof-advocate", accepted: true } as never); }),
    );
    const api = caller(`Bearer ${TOKEN}`);
    const first = api.proof.verify({ proofId: "proof-advocate" });
    await new Promise((resolve) => setTimeout(resolve, 5));
    await expect(api.proof.verify({ proofId: "proof-critic" })).rejects.toMatchObject({ code: "TOO_MANY_REQUESTS" });
    finish();
    await expect(first).resolves.toMatchObject({ accepted: true });
    await expect(api.proof.verify({ proofId: "proof-critic" })).resolves.toMatchObject({ accepted: true });
  });

  it("input is validated before use", async () => {
    process.env.REVIEWER_TOKEN = TOKEN;
    const api = caller(`Bearer ${TOKEN}`);
    await expect(api.proof.verify({ proofId: "x".repeat(65) })).rejects.toMatchObject({ code: "BAD_REQUEST" });
    await expect(api.workspace.setStatementStatus({ statementId: "A1", status: "approved", note: "x" }))
      .rejects.toMatchObject({ code: "BAD_REQUEST" });
    // @ts-expect-error an unknown status must be rejected at runtime too
    await expect(api.workspace.setStatementStatus({ statementId: "A1", status: "deleted", note: "testing" }))
      .rejects.toMatchObject({ code: "BAD_REQUEST" });
  });
});
