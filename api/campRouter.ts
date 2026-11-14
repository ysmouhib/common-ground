import { z } from "zod";

import { TRPCError } from "@trpc/server";

import { createRouter, reviewerMutation } from "./middleware";

import { engineGate, runCampReport } from "./engineRunner";

/** A camp name the engine accepts as a directory name (mirrors __main__._camp_dir). */
export const campName = z
  .string()
  .min(1)
  .max(64)
  .regex(/^[^/\\:*?"<>|]+$/, "the camp name must be a plain directory name")
  .refine(
    (name) =>
      name === name.trim() &&
      name !== "." &&
      name !== ".." &&
      !name.endsWith(".") &&
      ![...name].some((ch) => ch.charCodeAt(0) < 32),
    "the camp name must be a plain directory name",
  );

export const span = z.tuple([z.number().int().min(0), z.number().int().min(0)]);

export const recordSchema = z.object({
  camp: campName,
  documents: z
    .array(z.object({ id: z.string().min(1).max(200), text: z.string().min(1).max(50_000) }))
    .max(20),
  statements: z
    .array(
      z.object({
        id: z.string().min(1).max(64),
        stance: z.enum(["endorsed", "rejected_firm", "rejected_soft"]),
        fol: z.string().max(5000).nullable(),
        document: z.string().min(1).max(200),
        quote: z.string().max(5000),
        span,
      }),
    )
    .max(100),
});

export const candidatesSchema = z.object({
  candidates: z
    .array(
      z.object({
        fol: z.string().min(1).max(5000),
        quotes: z
          .array(z.object({ document: z.string().min(1).max(200), text: z.string().max(5000), span }))
          .max(20),
      }),
    )
    .max(64),
});

export const plausibility = z
  .union([z.number().min(0).max(1), z.tuple([z.number().min(0).max(1), z.number().min(0).max(1)])])
  .refine((value) => typeof value === "number" || value[0] <= value[1], "a plausibility range must satisfy min <= max");

export const campRouter = createRouter({
  /**
   * Run the engine's per-camp report on a reviewed record. Starting a Python
   * process sits behind the reviewer token, like starting Lean. The answer
   * carries search_complete, existence, per-system badge/certified and the
   * per-check outcomes — never an abstention or a headline badge alone. A
   * runtime that cannot run the engine answers no_verdict, which is not a
   * verdict about the record.
   */
  run: reviewerMutation
    .input(
      z.object({
        record: recordSchema,
        candidates: candidatesSchema,
        plausibilities: z
          .record(z.string().max(5000), plausibility)
          .refine((entries) => Object.keys(entries).length <= 256, "at most 256 plausibility entries")
          .optional(),
        lam: z.number().gt(0).max(10).default(0.3),
        maxChecks: z.number().int().min(1).max(100_000).default(4000),
        timeoutMs: z.number().int().min(500).max(60_000).default(5000),
        lean: z.boolean().default(false),
      }),
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
        const result = await runCampReport(input);
        if (result.kind === "invalid_input") {
          throw new TRPCError({ code: "BAD_REQUEST", message: `The engine rejected the input: ${result.message}` });
        }
        return result;
      } finally {
        release();
      }
    }),
});
