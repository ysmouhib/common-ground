import { and, eq } from "drizzle-orm";
import { getDb } from "../api/queries/connection";
import { log } from "../api/lib/logger";
import { debates, evidence, proofs, statements } from "./schema";
import { debateSeed, DEBATE_ID, evidenceSeed, proofSeed, seedCorrections, statementSeed } from "./seed-data";

/**
 * Apply seedCorrections. Each update is guarded by the old value, so running it
 * again, or on a row a reviewer has since changed, does nothing.
 */
export async function applyCorrections(): Promise<void> {
  const db = getDb();
  for (const fix of seedCorrections.evidence) {
    await db
      .update(evidence)
      .set({ [fix.field]: fix.to })
      .where(and(eq(evidence.id, fix.id), eq(evidence[fix.field], fix.from)));
  }
  for (const fix of seedCorrections.statementFormalText) {
    await db.update(statements).set({ formalText: fix.to }).where(and(eq(statements.id, fix.id), eq(statements.formalText, fix.from)));
  }
}

let correctionsDone = false;

export async function ensureSeeded(): Promise<void> {
  const db = getDb();

  // No-op upserts make first load safe under concurrent requests and repair a
  // partially imported baseline without replacing reviews or verification state.
  await db.insert(debates).values(debateSeed).onDuplicateKeyUpdate({ set: { id: debateSeed.id } });
  await db.insert(evidence).values(evidenceSeed).onDuplicateKeyUpdate({ set: { debateId: DEBATE_ID } });
  await db.insert(statements).values(statementSeed).onDuplicateKeyUpdate({ set: { debateId: DEBATE_ID } });
  await db.insert(proofs).values(proofSeed).onDuplicateKeyUpdate({ set: { debateId: DEBATE_ID } });
  // Once per process; a failure is logged and never blocks a page load.
  if (!correctionsDone) {
    correctionsDone = true;
    try {
      await applyCorrections();
    } catch (error) {
      log.error("seed corrections failed", { error: error instanceof Error ? error.message : String(error) });
    }
  }
}
