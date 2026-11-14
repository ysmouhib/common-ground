import { z } from "zod";

import { checkSchema } from "./engineReport";

/**
 * The part of the engine's crosscamp.json (engine/commonground/crosscamp.py,
 * analyze) that the API may surface. Same whitelist rule as engineReport.ts:
 * keys this schema does not name are stripped on parse, and `search_incomplete`
 * is a first-class field — a camp whose search the check budget stopped has its
 * selection-relative sections reported as provisional, never as findings.
 */

const unformalizedSchema = z.object({ camp: z.string(), id: z.string() });

// One pool statement every camp's premise set entails, with all its checks.
const agreedSchema = z.looseObject({
  statement: z.string(),
  origin: z.string(),
  id: z.string(),
  checks: z.array(checkSchema),
});

const rootDivergenceSchema = z.looseObject({
  camp1: z.string(),
  a1: z.string(),
  camp2: z.string(),
  a2: z.string(),
  rank: z.number(),
  rank_is_lower_bound: z.boolean(),
  checks: z.array(checkSchema),
});

const rootDivergencePendingSchema = z.looseObject({
  camp1: z.string(),
  a1: z.string(),
  camp2: z.string(),
  a2: z.string(),
  pending: z.string(),
});

export const crosscampReportSchema = z.object({
  camps: z.array(z.string()),
  search_incomplete: z.array(z.string()),
  common_ground: z.object({
    camps: z.array(z.string()),
    stated: z.looseObject({
      agreed: z.array(agreedSchema),
      union_consistent: checkSchema,
      camp_consistency: z.array(z.looseObject({ camp: z.string() })),
      vacuous_camps: z.array(z.string()),
      pending_camps: z.array(z.string()),
      unformalized: z.array(unformalizedSchema),
      pool: z.array(z.string()),
    }),
    per_system_pair: z.array(
      z.looseObject({
        camps: z.array(z.string()),
        systems: z.array(z.array(z.string())),
        agreed: z.array(agreedSchema),
      }),
    ),
    no_certified_systems: z.array(z.string()),
  }),
  fault_lines: z.object({
    stated: z.looseObject({
      consistent: checkSchema,
      mus: z.array(z.array(z.string())).nullable(),
      mcs: z.array(z.array(z.string())).nullable(),
      pending: z.string().optional(),
      unformalized: z.array(unformalizedSchema),
      complete: z.boolean(),
    }),
    per_system_pair: z.array(
      z.looseObject({
        camps: z.array(z.string()),
        systems: z.array(z.array(z.string())),
        mus: z.array(z.array(z.string())).nullable(),
        mcs: z.array(z.array(z.string())).nullable(),
        consistent: z.boolean().nullable(),
        pending: z.string().optional(),
        root_divergence: z.array(rootDivergenceSchema),
        root_divergence_pending: z.array(rootDivergencePendingSchema),
      }),
    ),
    no_certified_systems: z.array(z.string()),
  }),
});

export type CrosscampReport = z.infer<typeof crosscampReportSchema>;

/** Parse and whitelist one crosscamp.json. Throws when a required field is missing. */
export function parseCrosscampReport(raw: unknown): CrosscampReport {
  return crosscampReportSchema.parse(raw);
}
