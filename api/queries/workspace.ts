import { asc, desc, eq } from "drizzle-orm";
import { createHash } from "node:crypto";
import {
  aiDrafts,
  debates,
  evidence,
  proofs,
  reviewEvents,
  statements,
  verificationRuns,
} from "@db/schema";
import { ensureSeeded } from "@db/seed-logic";
import { DEBATE_ID } from "@db/seed-data";
import { buildLeanSource, buildNegativeControlSource } from "@contracts/lean";
import { analysis as logic } from "@contracts/analysis.generated";
import { getDb } from "./connection";

function sourceHash(proof: typeof proofs.$inferSelect): string {
  const source = proof.isNegativeControl
    ? buildNegativeControlSource()
    : buildLeanSource(proof.theoremName);
  return createHash("sha256").update(source).digest("hex");
}

export async function getWorkspace() {
  await ensureSeeded();
  const db = getDb();
  const [debate] = await db.select().from(debates).where(eq(debates.id, DEBATE_ID)).limit(1);
  const allEvidence = await db.select().from(evidence).where(eq(evidence.debateId, DEBATE_ID)).orderBy(asc(evidence.id));
  const allStatements = await db
    .select()
    .from(statements)
    .where(eq(statements.debateId, DEBATE_ID))
    .orderBy(asc(statements.sortOrder));
  const allProofs = await db.select().from(proofs).where(eq(proofs.debateId, DEBATE_ID));
  const events = await db.select().from(reviewEvents).orderBy(desc(reviewEvents.createdAt)).limit(40);
  const drafts = await db.select().from(aiDrafts).orderBy(desc(aiDrafts.createdAt)).limit(20);
  const runs = await db.select().from(verificationRuns).orderBy(desc(verificationRuns.createdAt)).limit(30);

  const statementById = new Map(allStatements.map((statement) => [statement.id, statement]));
  const enrichedProofs = allProofs
    .map((proof) => {
      const hashCurrent = proof.proofHash === sourceHash(proof);
      const kernelVerified = proof.status === "verified" && hashCurrent;
      const missingPremiseIds = proof.premiseIds.filter(
        (id) => statementById.get(id)?.approvalStatus !== "approved",
      );
      const active = !proof.isNegativeControl && kernelVerified && missingPremiseIds.length === 0;
      return {
        ...proof,
        hashCurrent,
        kernelVerified,
        missingPremiseIds,
        active,
        certificateState: proof.isNegativeControl
          ? ("negative_control" as const)
          : active
            ? ("active" as const)
            : kernelVerified
              ? ("inactive" as const)
              : ("unverified" as const),
      };
    })
    .sort((a, b) => Number(a.isNegativeControl) - Number(b.isNegativeControl) || a.id.localeCompare(b.id));

  const activeProofIds = new Set(enrichedProofs.filter((proof) => proof.active).map((proof) => proof.id));
  const negativeControl = enrichedProofs.find((proof) => proof.isNegativeControl);

  return {
    debate,
    evidence: allEvidence,
    statements: allStatements,
    proofs: enrichedProofs,
    reviewEvents: events.filter((event) => statementById.has(event.statementId)),
    aiDrafts: drafts.filter((draft) => statementById.has(draft.statementId)),
    verificationRuns: runs,
    analysis: {
      activeProofCount: activeProofIds.size,
      verifiedProofCount: enrichedProofs.filter((proof) => proof.kernelVerified).length,
      disputedCount: allStatements.filter((statement) => statement.approvalStatus === "disputed").length,
      approvedCount: allStatements.filter((statement) => statement.approvalStatus === "approved").length,
      advocateActive: activeProofIds.has("proof-advocate"),
      criticActive: activeProofIds.has("proof-critic"),
      sharedGroundActive: activeProofIds.has("proof-shared"),
      combinedActive: activeProofIds.has("proof-combined"),
      negativeControlRejected: negativeControl?.status === "failed" && negativeControl.hashCurrent,
      // Computed by the logic engine (engine/commonground/argmap.py) and stored in
      // contracts/analysis.generated.ts; nothing below is asserted by hand.
      // "Compatible" means: all premises of both positions have a common model.
      positionsCompatible: logic.positions_compatible,
      conflicts: logic.conflicts,
      minimalConcessions: logic.minimal_concessions,
      disagreementKind: !logic.positions_compatible
        ? ("contradiction" as const)
        : activeProofIds.has("proof-advocate") && activeProofIds.has("proof-critic")
          ? ("priority_not_contradiction" as const)
          : ("premises_under_review" as const),
    },
  };
}

export type Workspace = Awaited<ReturnType<typeof getWorkspace>>;
