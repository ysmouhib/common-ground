import { createOpenAICompatible } from "@ai-sdk/openai-compatible";
import { generateObject } from "ai";
import { eq } from "drizzle-orm";
import { z } from "zod";
import { TRPCError } from "@trpc/server";
import { aiDrafts, evidence, reviewEvents, statements } from "@db/schema";
import { createRouter, publicQuery } from "./middleware";
import { getDb } from "./queries/connection";
import {
  AiInvalidRequest,
  AiMisconfigured,
  AiTransient,
  AiUnavailable,
  classifyAiError,
  ContentRejected,
  listModels,
} from "./ai-client";

function aiError(error: unknown): never {
  const classified = classifyAiError(error);
  if (classified instanceof AiUnavailable) {
    throw new TRPCError({
      code: "FORBIDDEN",
      message: "AI formalization is unavailable because the site’s AI quota or entitlement is exhausted. Manual review remains available.",
    });
  }
  if (classified instanceof ContentRejected || classified instanceof AiInvalidRequest) {
    throw new TRPCError({ code: "BAD_REQUEST", message: classified.message });
  }
  if (classified instanceof AiMisconfigured) {
    throw new TRPCError({
      code: "PRECONDITION_FAILED",
      message: "AI is not provisioned for this site. Reopen or publish the site once, then retry; manual review remains available.",
    });
  }
  if (classified instanceof AiTransient) {
    throw new TRPCError({
      code: "TIMEOUT",
      message: "The AI service is temporarily unavailable. No automatic retry was made; retry deliberately when ready.",
    });
  }
  throw classified;
}

export const aiRouter = createRouter({
  critiqueFormalization: publicQuery
    .input(z.object({ statementId: z.string().min(1).max(64) }))
    .mutation(async ({ input }) => {
      const db = getDb();
      const [statement] = await db.select().from(statements).where(eq(statements.id, input.statementId)).limit(1);
      if (!statement) throw new TRPCError({ code: "NOT_FOUND", message: "Statement not found." });
      const linkedEvidence = statement.evidenceId
        ? (await db.select().from(evidence).where(eq(evidence.id, statement.evidenceId)).limit(1))[0]
        : undefined;

      try {
        const { defaultModelId } = await listModels();
        const provider = createOpenAICompatible({
          name: "kimi-gw",
          baseURL: process.env.KIMI_AGENTGW_BASE_URL!,
          apiKey: process.env.KIMI_AGENTGW_API_KEY!,
          supportsStructuredOutputs: true,
        });
        const result = await generateObject({
          model: provider(defaultModelId),
          schema: z.object({
            proposedFormal: z.string().min(1).max(1500),
            backTranslation: z.string().min(1).max(2000),
            interpretationNotes: z.array(z.string().min(1).max(500)).min(1).max(5),
          }),
          prompt: `You are reviewing a human-owned formalization in a political argument explorer. Propose a careful formal reading, but do not certify truth and do not invent evidence. Use only simple propositional or first-order Lean-style notation. Flag ambiguity, scope loss, and normative assumptions. The current formalization may already be appropriate; you may retain it.

Original statement: ${statement.body}
Statement kind: ${statement.kind}
Current formalization: ${statement.formalText}
Existing formalization note: ${statement.formalizationNote}
Evidence finding: ${linkedEvidence?.finding ?? "No linked evidence"}
Evidence limitation: ${linkedEvidence?.limitation ?? "No linked evidence"}

Return a proposed formal expression, a plain-language back-translation, and 1–5 concise interpretation notes.`,
          providerOptions: { "kimi-gw": { max_completion_tokens: 1600, reasoning_effort: "low" } },
        });
        const notes = result.object.interpretationNotes.join("\n");
        const [inserted] = await db.insert(aiDrafts).values({
          statementId: statement.id,
          proposedFormal: result.object.proposedFormal,
          backTranslation: result.object.backTranslation,
          interpretationNotes: notes,
        }).$returningId();
        await db.insert(reviewEvents).values({
          statementId: statement.id,
          action: "ai_draft_created",
          note: "AI proposed an alternative reading. No canonical statement or proof was changed.",
        });
        return {
          id: inserted.id,
          statementId: statement.id,
          ...result.object,
          interpretationNotes: notes,
        };
      } catch (error) {
        aiError(error);
      }
    }),
});
