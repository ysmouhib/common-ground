import { describe, expect, it } from "vitest";

import { parseCampReport, parseEngineJson } from "./engineReport";

function rawReport(): Record<string, unknown> {
  const check = {
    kind: "sufficiency",
    claim: "Mortal(socrates)",
    outcome: "holds",
    badge: "SOLVER-CHECKED (not kernel-certified)",
    detail: "solver refutation",
    model: null,
    certificate: null,
  };
  return {
    camp: "yes",
    lam: 0.3,
    source: "scripted",
    statements: [{ id: "yes-1", stance: "endorsed", fol: "P", document: "d1", span: [0, 1] }],
    pool: { candidates: [], dropped: [] },
    search_complete: false,
    hull_complete: false,
    existence: { status: "pending", reason: "unformalized", detail: "1 statement(s) unformalized", unformalized: ["yes-2"] },
    selection: {
      lam: 0.3,
      best_cost: 1.2,
      systems: [["A", "B"]],
      all_certified: [["A", "B"]],
      checks: 17,
      exhausted: true,
    },
    systems: [
      {
        axioms: ["A", "B"],
        cost: 1.2,
        certified: true,
        badge: "SOLVER-CHECKED (1 of 2 entailments kernel-checked)",
        checks: {
          consistent: { ...check, kind: "consistency", claim: "(consistency)" },
          sufficiency: [check],
          firm_rejections: [],
          soft_rejections: [{ ...check, kind: "soft_rejection", outcome: "fails" }],
          minimality: [],
          certified: true,
        },
        load: [{ axiom: "A", removals_undecided: [] }],
        negative_controls: [],
      },
    ],
    // Everything below this line must NOT reach the API: the whitelist strips it.
    abstention: { lam: 0.3, decision: "abstain" },
    baseline: { stated_certified: true },
    hull: [{ systems: [["A", "B"]], interval: [0, 0.4] }],
    coverage: { kappa: 1 },
    plausibility_sensitivity: { stable: true },
    warnings: [],
  };
}

describe("the camp report contract", () => {
  it("surfaces search completeness, existence, per-system badges and per-check outcomes", () => {
    const report = parseCampReport(rawReport());
    expect(report.camp).toBe("yes");
    expect(report.search_complete).toBe(false);
    expect(report.hull_complete).toBe(false);
    expect(report.existence).toMatchObject({ status: "pending", reason: "unformalized" });
    expect(report.selection.exhausted).toBe(true);
    expect(report.systems).toHaveLength(1);
    expect(report.systems[0].certified).toBe(true);
    expect(report.systems[0].badge).toBe("SOLVER-CHECKED (1 of 2 entailments kernel-checked)");
    expect(report.systems[0].checks.certified).toBe(true);
    expect(report.systems[0].checks.sufficiency[0].outcome).toBe("holds");
    expect(report.systems[0].checks.soft_rejections[0].outcome).toBe("fails");
  });

  it("strips every key it does not name, abstention included", () => {
    const report = parseCampReport(rawReport());
    expect("abstention" in report).toBe(false);
    expect(Object.keys(report).sort()).toEqual(
      ["camp", "existence", "hull_complete", "lam", "search_complete", "selection", "systems"].sort(),
    );
  });

  it("rejects a report without the search-completeness flag", () => {
    const raw = rawReport();
    delete raw.search_complete;
    expect(() => parseCampReport(raw)).toThrow();
  });

  it("rejects a report whose existence has no status", () => {
    const raw = rawReport();
    raw.existence = { reason: "unformalized" };
    expect(() => parseCampReport(raw)).toThrow();
  });

  it("rejects an unknown per-check outcome", () => {
    const raw = rawReport();
    const systems = raw.systems as Array<{ checks: { sufficiency: Array<{ outcome: string }> } }>;
    systems[0].checks.sufficiency[0].outcome = "maybe";
    expect(() => parseCampReport(raw)).toThrow();
  });
});

describe("parsing the engine's JSON text", () => {
  it("reads Python's bare Infinity/NaN tokens as null, but not inside strings", () => {
    const parsed = parseEngineJson(
      '{"interval": [0.0, Infinity], "note": "the end is Infinity, not NaN", "vals": [NaN, -Infinity]}',
    );
    expect(parsed).toEqual({
      interval: [0.0, null],
      note: "the end is Infinity, not NaN",
      vals: [null, null],
    });
  });

  it("keeps escaped quotes intact while scanning", () => {
    const parsed = parseEngineJson('{"detail": "a \\"quoted\\" Infinity", "n": NaN}');
    expect(parsed).toEqual({ detail: 'a "quoted" Infinity', n: null });
  });
});
