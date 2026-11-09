import { eq } from "drizzle-orm";
import { z } from "zod";
import { TRPCError } from "@trpc/server";
import { createRouter, publicQuery, reviewerMutation } from "./middleware";
import { getWorkspace } from "./queries/workspace";
import { getDb } from "./queries/connection";
import { reviewEvents, statements } from "@db/schema";

export const workspaceRouter = createRouter({
  get: publicQuery.query(async ({ ctx }) => ({
    ...(await getWorkspace()),
    // Lets the interface show review controls only to someone who can use them.
    access: { reviewEnabled: ctx.access.reviewEnabled, isReviewer: ctx.access.isReviewer },
  })),
  setStatementStatus: reviewerMutation
    .input(
      z.object({
        statementId: z.string().min(1).max(64),
        status: z.enum(["approved", "disputed", "draft"]),
        note: z.string().trim().min(3).max(1000),
      }),
    )
    .mutation(async ({ input }) => {
      const db = getDb();
      const [statement] = await db
        .select()
        .from(statements)
        .where(eq(statements.id, input.statementId))
        .limit(1);
      if (!statement) {
        throw new TRPCError({ code: "NOT_FOUND", message: "Statement not found." });
      }
      await db.transaction(async (tx) => {
        await tx
          .update(statements)
          .set({ approvalStatus: input.status })
          .where(eq(statements.id, input.statementId));
        await tx.insert(reviewEvents).values({
          statementId: input.statementId,
          action: input.status,
          note: input.note,
        });
      });
      return { ok: true };
    }),
});
