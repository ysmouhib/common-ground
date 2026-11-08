import { z } from "zod";
import { createRouter, publicQuery } from "./middleware";
import { verifyProof } from "./proofVerifier";

export const proofRouter = createRouter({
  verify: publicQuery
    .input(z.object({ proofId: z.string().min(1).max(64) }))
    .mutation(({ input }) => verifyProof(input.proofId)),
  verifyAll: publicQuery.mutation(async () => {
    const results = [];
    for (const id of ["proof-advocate", "proof-critic", "proof-shared", "proof-combined", "negative-overreach"]) {
      results.push(await verifyProof(id));
    }
    return results;
  }),
});
