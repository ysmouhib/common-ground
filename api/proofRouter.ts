import { z } from "zod";
import { TRPCError } from "@trpc/server";
import { createRouter, reviewerMutation } from "./middleware";
import { leanGate } from "./lib/security";
import { verifyProof } from "./proofVerifier";

/** One Lean run at a time: each starts a process, and a second request is refused, not queued. */
async function withLean<T>(run: () => Promise<T>): Promise<T> {
  const release = leanGate.tryEnter();
  if (!release) {
    throw new TRPCError({
      code: "TOO_MANY_REQUESTS",
      message: "A Lean verification is already running. Try again when it has finished.",
    });
  }
  try {
    return await run();
  } finally {
    release();
  }
}

export const proofRouter = createRouter({
  verify: reviewerMutation
    .input(z.object({ proofId: z.string().min(1).max(64) }))
    .mutation(({ input }) => withLean(() => verifyProof(input.proofId))),
  verifyAll: reviewerMutation.mutation(() =>
    withLean(async () => {
      const results = [];
      for (const id of ["proof-advocate", "proof-critic", "proof-shared", "proof-combined", "negative-overreach"]) {
        results.push(await verifyProof(id));
      }
      return results;
    }),
  ),
});
