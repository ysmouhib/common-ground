import { useCallback, useState } from "react";

import type { CampReport } from "@contracts/engineReport";

/**
 * Human review decisions over the proposed axioms of one camp report (CG6-3).
 * A model proposes; a human approves or rejects — no model output reaches the
 * Lean kernel without a decision recorded here.
 */

export type AxiomDecision = {
  status: "approved" | "rejected";
  note: string;
  at: string;
};

export function useAxiomQueue() {
  const [decisions, setDecisions] = useState<Record<string, AxiomDecision>>({});

  const decide = useCallback((fol: string, status: "approved" | "rejected", note: string) => {
    setDecisions((current) => ({
      ...current,
      [fol]: { status, note, at: new Date().toISOString() },
    }));
  }, []);

  const clearDecisions = useCallback(() => setDecisions({}), []);

  return { decisions, decide, clearDecisions };
}

/** Every proposed axiom of the report has a human decision. */
export function allDecided(report: CampReport, decisions: Record<string, AxiomDecision>): boolean {
  return report.pool.candidates.every((candidate) => decisions[candidate.fol] !== undefined);
}

/**
 * The approved candidates as the engine's candidates JSON
 * ({"candidates": [{"fol", "quotes": [{"document", "text", "span"}]}]}) — the input
 * of the next, kernel-checked run.
 */
export function approvedCandidatesJson(
  report: CampReport,
  decisions: Record<string, AxiomDecision>,
): { candidates: { fol: string; quotes: { document: string; text: string; span: [number, number] }[] }[] } {
  return {
    candidates: report.pool.candidates
      .filter((candidate) => decisions[candidate.fol]?.status === "approved")
      .map((candidate) => ({
        fol: candidate.fol,
        quotes: candidate.quotes.map(([document, text, span]) => ({ document, text, span })),
      })),
  };
}
