import { z } from "zod";

/**
 * The part of the engine's extract output (engine/commonground/extract.py:
 * summary.json + runs.jsonl) that the API may surface. Every returned statement
 * carries its verbatim span in the source text — the engine validates that the
 * span's text equals the statement before accepting it. A provider outage stops
 * the run (engine exit 3) and is surfaced by the bridge as no_verdict, never as
 * a wrong answer; per-document failures appear as rows with an `error` field.
 */

export const extractRowSchema = z.looseObject({
  document: z.string(),
  statements: z
    .array(z.object({ text: z.string(), span: z.tuple([z.number(), z.number()]) }))
    .optional(),
  relations: z
    .array(z.object({ from: z.array(z.string()), to: z.array(z.string()), kind: z.string() }))
    .optional(),
  error: z.string().optional(),
  attempts: z.number().optional(),
});

export const extractSummarySchema = z.looseObject({
  mode: z.string(),
  documents: z.number(),
  statements: z.number(),
  relations: z.number(),
  failed: z.number(),
});

export const extractRunSchema = z.object({
  summary: extractSummarySchema,
  rows: z.array(extractRowSchema),
});

export type ExtractRow = z.infer<typeof extractRowSchema>;
export type ExtractSummary = z.infer<typeof extractSummarySchema>;
export type ExtractRun = z.infer<typeof extractRunSchema>;

/** Parse and whitelist one extract run (summary.json plus every runs.jsonl row). */
export function parseExtractRun(summary: unknown, rows: unknown[]): ExtractRun {
  return extractRunSchema.parse({ summary, rows });
}
