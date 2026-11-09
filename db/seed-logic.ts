import { and, eq } from "drizzle-orm";
import { getDb } from "../api/queries/connection";
import { log } from "../api/lib/logger";
import { debates, evidence, proofs, statements } from "./schema";
import { debateSeed, DEBATE_ID, evidenceSeed, proofSeed, seedCorrections, statementSeed } from "./seed-data";

let correctionsApplied = false;

/** Apply seedCorrections once per process. A failure is logged and never blocks a page load. */
async function applyCorrections(): Promise<void> {
  if (correctionsApplied) return;
  correctionsApplied = true;
  const db = getDb();
  try {
    for (const fix of seedCorrections.evidenceExcerpt) {
      await db.update(evidence).set({ excerpt: fix.to }).where(and(eq(evidence.id, fix.id), eq(evidence.excerpt, fix.from)));
    }
    for (const fix of seedCorrections.evidencePublishedAt) {
      await db.update(evidence).set({ publishedAt: fix.to }).where(and(eq(evidence.id, fix.id), eq(evidence.publishedAt, fix.from)));
    }
    for (const fix of seedCorrections.statementFormalText) {
      await db.update(statements).set({ formalText: fix.to }).where(and(eq(statements.id, fix.id), eq(statements.formalText, fix.from)));
    }
  } catch (error) {
    log.error("seed corrections failed", { error: error instanceof Error ? error.message : String(error) });
  }
}

export async function ensureSeeded(): Promise<void> {
  const db = getDb();

  // No-op upserts make first load safe under concurrent requests and repair a
  // partially imported baseline without replacing reviews or verification state.
  await db.insert(debates).values(debateSeed).onDuplicateKeyUpdate({ set: { id: debateSeed.id } });
  await db.insert(evidence).values(evidenceSeed).onDuplicateKeyUpdate({ set: { debateId: DEBATE_ID } });
  await db.insert(statements).values(statementSeed).onDuplicateKeyUpdate({ set: { debateId: DEBATE_ID } });
  await db.insert(proofs).values(proofSeed).onDuplicateKeyUpdate({ set: { debateId: DEBATE_ID } });
  await applyCorrections();
}
