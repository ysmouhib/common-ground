import { readFileSync } from "node:fs";
import path from "node:path";
import { describe, expect, it } from "vitest";
import { analysis } from "./analysis.generated";
import { leanProofs } from "./lean";
import { statementSeed } from "../db/seed-data";

const example = JSON.parse(
  readFileSync(path.resolve(import.meta.dirname, "../engine/examples/plastic_bags.json"), "utf8"),
) as { statements: { id: string; owner: string; kind: string; fol: string | null }[] };

describe("computed analysis of the worked example", () => {
  it("analyses the same statements the app shows", () => {
    expect(example.statements.map(({ id, owner, kind }) => ({ id, owner, kind })))
      .toEqual(statementSeed.map(({ id, owner, kind }) => ({ id, owner, kind })));
    const premises = example.statements.filter((s) => s.kind !== "conclusion" && s.fol !== null).map((s) => s.id).sort();
    expect([...analysis.premise_ids]).toEqual(premises);
    expect([...analysis.statements_without_formula]).toEqual(["D1"]);
  });

  it("finds the two positions compatible, with a re-checked model as evidence", () => {
    expect(analysis.positions_compatible).toBe(true);
    expect(analysis.conflicts).toHaveLength(0);
    expect(analysis.compatibility_witness?.rechecked_by_independent_evaluator).toBe(true);
  });

  it("derives each proof's premise list instead of trusting the declared one", () => {
    // The declared premises of every Lean proof are exactly the one minimal set of
    // premises that entails its conclusion: nothing is missing and nothing is idle.
    for (const proof of leanProofs) {
      const computed = analysis.conclusions[proof.conclusionId as keyof typeof analysis.conclusions];
      expect(computed.from_all_premises).toBe("True");
      expect(computed.justifications.map((j) => [...j])).toEqual([[...proof.premiseIds].sort()]);
    }
  });
});
