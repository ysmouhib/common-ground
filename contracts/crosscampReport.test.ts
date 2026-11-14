import { describe, expect, it } from "vitest";

import { parseCrosscampReport } from "./crosscampReport";
import { parseExtractRun } from "./extractRun";

const check = {
  kind: "consistency",
  claim: "(consistency)",
  outcome: "holds",
  badge: "SOLVER-CHECKED (not kernel-certified)",
  detail: "explicit finite model",
};

function rawCrosscamp(): Record<string, unknown> {
  return {
    camps: ["yes", "no"],
    search_incomplete: ["yes"],
    common_ground: {
      camps: ["yes", "no"],
      stated: {
        agreed: [{ statement: "P", origin: "yes", id: "yes-1", checks: [check] }],
        union_consistent: check,
        camp_consistency: [{ camp: "yes", ...check }, { camp: "no", ...check }],
        vacuous_camps: [],
        pending_camps: [],
        unformalized: [{ camp: "yes", id: "yes-5" }],
        pool: ["P"],
      },
      per_system_pair: [
        {
          camps: ["yes", "no"],
          systems: [["A"], ["B"]],
          agreed: [{ statement: "Q", origin: "pool", id: "c1", checks: [check, check], derivations: [["A", "B"]] }],
        },
      ],
      no_certified_systems: [],
    },
    fault_lines: {
      stated: {
        consistent: check,
        mus: [["A", "¬A"]],
        mcs: [["A"]],
        unformalized: [],
        complete: true,
      },
      per_system_pair: [
        {
          camps: ["yes", "no"],
          systems: [["A"], ["B"]],
          mus: [["A", "B"]],
          mcs: [["A"]],
          consistent: false,
          root_divergence: [
            { camp1: "yes", a1: "A", camp2: "no", a2: "B", rank: 8, rank_is_lower_bound: false, checks: [check, check] },
          ],
          root_divergence_pending: [{ camp1: "yes", a1: "A", camp2: "no", a2: "C", pending: "non-entailment undecided" }],
        },
      ],
      no_certified_systems: [],
    },
    // must be stripped: the whitelist does not name it
    abstention: { yes: true },
    per_camp_abstention: ["yes"],
  };
}

describe("the cross-camp report contract", () => {
  it("surfaces search_incomplete, both tiers, fault lines and pending root pairs", () => {
    const report = parseCrosscampReport(rawCrosscamp());
    expect(report.camps).toEqual(["yes", "no"]);
    expect(report.search_incomplete).toEqual(["yes"]);
    expect(report.common_ground.stated.agreed[0].statement).toBe("P");
    expect(report.common_ground.stated.unformalized).toEqual([{ camp: "yes", id: "yes-5" }]);
    expect(report.common_ground.per_system_pair[0].agreed[0].checks).toHaveLength(2);
    expect(report.fault_lines.stated.mus).toEqual([["A", "¬A"]]);
    expect(report.fault_lines.per_system_pair[0].root_divergence[0].rank).toBe(8);
    expect(report.fault_lines.per_system_pair[0].root_divergence_pending[0].pending).toBe(
      "non-entailment undecided",
    );
  });

  it("strips every key it does not name, abstention included", () => {
    const report = parseCrosscampReport(rawCrosscamp());
    expect("abstention" in report).toBe(false);
    expect("per_camp_abstention" in report).toBe(false);
  });

  it("accepts a pending stated tier (mus/mcs null with a reason)", () => {
    const raw = rawCrosscamp();
    const fl = raw.fault_lines as { stated: Record<string, unknown> };
    fl.stated.mus = null;
    fl.stated.mcs = null;
    fl.stated.pending = "no verdict: enumeration stopped";
    const report = parseCrosscampReport(raw);
    expect(report.fault_lines.stated.mus).toBeNull();
    expect(report.fault_lines.stated.pending).toBe("no verdict: enumeration stopped");
  });

  it("rejects a report without search_incomplete", () => {
    const raw = rawCrosscamp();
    delete raw.search_incomplete;
    expect(() => parseCrosscampReport(raw)).toThrow();
  });
});

describe("the extract run contract", () => {
  it("surfaces per-document statements with their verbatim spans and relations", () => {
    const run = parseExtractRun(
      { mode: "extract", documents: 1, statements: 1, relations: 1, failed: 0 },
      [
        {
          document: "doc1",
          statements: [{ text: "Bags cause litter", span: [0, 17] }],
          relations: [{ from: ["s1"], to: ["s2"], kind: "support" }],
          attempts: 1,
        },
      ],
    );
    expect(run.summary.documents).toBe(1);
    expect(run.rows[0].statements?.[0].span).toEqual([0, 17]);
    expect(run.rows[0].relations?.[0].kind).toBe("support");
  });

  it("keeps a per-document failure as an error row, not as a verdict", () => {
    const run = parseExtractRun(
      { mode: "extract", documents: 1, statements: 0, relations: 0, failed: 1 },
      [{ document: "doc1", error: "NoExtraction", attempts: 3 }],
    );
    expect(run.summary.failed).toBe(1);
    expect(run.rows[0].error).toBe("NoExtraction");
    expect(run.rows[0].statements).toBeUndefined();
  });

  it("rejects a summary without its counts", () => {
    expect(() => parseExtractRun({ mode: "extract" }, [])).toThrow();
  });
});
