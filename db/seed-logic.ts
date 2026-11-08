import { getDb } from "../api/queries/connection";
import { debates, evidence, proofs, statements } from "./schema";
import { debateSeed, DEBATE_ID, evidenceSeed, proofSeed, statementSeed } from "./seed-data";

export async function ensureSeeded(): Promise<void> {
  const db = getDb();

  // No-op upserts make first load safe under concurrent requests and repair a
  // partially imported baseline without replacing reviews or verification state.
  await db.insert(debates).values(debateSeed).onDuplicateKeyUpdate({ set: { id: debateSeed.id } });
  await db.insert(evidence).values(evidenceSeed).onDuplicateKeyUpdate({ set: { debateId: DEBATE_ID } });
  await db.insert(statements).values(statementSeed).onDuplicateKeyUpdate({ set: { debateId: DEBATE_ID } });
  await db.insert(proofs).values(proofSeed).onDuplicateKeyUpdate({ set: { debateId: DEBATE_ID } });
}
