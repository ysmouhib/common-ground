import { z } from "zod";

/**
 * The part of the engine's per-camp report.json (engine/commonground/abduce.py,
 * report_camp) that the API may surface. This schema is a whitelist: keys it does
 * not name — among them `abstention` — are stripped on parse, so no abstention or
 * headline badge can reach a client through this type. The API shows
 * search_complete, existence, per-system badge/certified and the per-check
 * outcomes (soundness review 2026-11-14).
 */

// One certified check of one system (abduce.Check.to_json). The evidence models and
// the Lean certificate stay in the engine's report.json on disk.
export const checkSchema = z.object({
  kind: z.string(),
  claim: z.string(),
  outcome: z.enum(["holds", "fails", "pending"]),
  badge: z.string(),
  detail: z.string(),
});

const systemChecksSchema = z.object({
  consistent: checkSchema,
  sufficiency: z.array(checkSchema),
  firm_rejections: z.array(checkSchema),
  soft_rejections: z.array(checkSchema),
  minimality: z.array(checkSchema),
  certified: z.boolean(),
});

const systemSchema = z.object({
  axioms: z.array(z.string()),
  cost: z.number(),
  certified: z.boolean(),
  badge: z.string(),
  checks: systemChecksSchema,
});

// "none" and "pending" carry their reason and detail; the engine may add evidence
// keys (e.g. the unformalized statement ids), so these two objects are loose.
const existenceSchema = z.looseObject({
  status: z.enum(["certified", "none", "pending"]),
  reason: z.string().optional(),
  detail: z.string().optional(),
});

const selectionSchema = z.looseObject({
  lam: z.number(),
  best_cost: z.number().nullable(),
  systems: z.array(z.array(z.string())),
  all_certified: z.array(z.array(z.string())),
  checks: z.number(),
  exhausted: z.boolean(),
});

export const campReportSchema = z.object({
  camp: z.string(),
  lam: z.number(),
  search_complete: z.boolean(),
  hull_complete: z.boolean(),
  existence: existenceSchema,
  selection: selectionSchema,
  systems: z.array(systemSchema),
});

export type CampReport = z.infer<typeof campReportSchema>;

/** Parse and whitelist one report.json. Throws when a required field is missing. */
export function parseCampReport(raw: unknown): CampReport {
  return campReportSchema.parse(raw);
}

/**
 * JSON.parse for the engine's report.json. Python's json emits the bare tokens
 * Infinity / NaN for non-finite floats (e.g. the unbounded end of a λ-interval),
 * which strict JSON.parse rejects. Outside string literals they are read as
 * null; inside strings they are left untouched.
 */
export function parseEngineJson(text: string): unknown {
  let out = "";
  let inString = false;
  let i = 0;
  while (i < text.length) {
    const ch = text[i];
    if (inString) {
      out += ch;
      if (ch === "\\") {
        out += text[i + 1] ?? "";
        i += 2;
        continue;
      }
      if (ch === '"') inString = false;
      i += 1;
      continue;
    }
    if (ch === '"') {
      inString = true;
      out += ch;
      i += 1;
      continue;
    }
    if (ch === "-" && text.startsWith("Infinity", i + 1)) {
      out += "null";
      i += 9;
      continue;
    }
    if (text.startsWith("Infinity", i)) {
      out += "null";
      i += 8;
      continue;
    }
    if (text.startsWith("NaN", i)) {
      out += "null";
      i += 3;
      continue;
    }
    out += ch;
    i += 1;
  }
  return JSON.parse(out);
}
