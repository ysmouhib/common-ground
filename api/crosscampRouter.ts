import { z } from "zod";

import { TRPCError } from "@trpc/server";

import { createRouter, reviewerMutation } from "./middleware";

import { engineGate, runCrosscamp } from "./engineRunner";

import { candidatesSchema, plausibility, recordSchema } from "./campRouter";

/**
 * Cross-camp analysis on the same engine bridge as camp.run: two or more reviewed
 * records, one candidates file each, in the same order. Starting Python processes
 * sits behind the reviewer token. The answer carries the cross-camp report plus
 * each camp's whitelisted report — search_incomplete included, never an
 * abstention — and a runtime that cannot run the engine answers no_verdict.
 */
export const crosscampRouter = createRouter({
  run: reviewerMutation
    .input(
      z
        .object({
          records: z.array(recordSchema).min(2).max(8),
          candidates: z.array(candidatesSchema).min(2).max(8),
          plausibilities: z
            .record(z.string().max(5000), plausibility)
            .refine((entries) => Object.keys(entries).length <= 256, "at most 256 plausibility entries")
            .optional(),
          lam: z.number().gt(0).max(10).default(0.3),
          maxChecks: z.number().int().min(1).max(100_000).default(4000),
          timeoutMs: z.number().int().min(500).max(60_000).default(5000),
          lean: z.boolean().default(false),
        })
        .refine(
          (input) => input.records.length === input.candidates.length,
          "one candidates file per record, in the same order",
        ),
    )
    .mutation(async ({ input }) => {
      const release = engineGate.tryEnter();
      if (!release) {
        throw new TRPCError({
          code: "TOO_MANY_REQUESTS",
          message: "An engine report is already being computed. Try again when it has finished.",
        });
      }
      try {
        const result = await runCrosscamp(input);
        if (result.kind === "invalid_input") {
          throw new TRPCError({ code: "BAD_REQUEST", message: `The engine rejected the input: ${result.message}` });
        }
        return result;
      } finally {
        release();
      }
    }),
});
