import { initTRPC, TRPCError } from "@trpc/server";
import superjson from "superjson";
import type { TrpcContext } from "./context";
import { log } from "./lib/logger";
import { authFailures } from "./lib/security";

const t = initTRPC.context<TrpcContext>().create({
  transformer: superjson,
  // G9: a procedure that throws never reaches app.onError — the tRPC fetch
  // adapter catches it and returns its own 500 JSON, so the Hono error handler
  // is bypassed entirely. That left the most common real failure (a mutation
  // 500ing) with NO structured record in app.log on the server side; it only
  // appeared if the caller happened to log it in its own catch. This hook is the
  // missing server-side safety net. INTERNAL_SERVER_ERROR only: a thrown
  // TRPCError like UNAUTHORIZED is a deliberate business answer, not a crash,
  // and logging those would drown the file.
  errorFormatter({ shape, error }) {
    if (error.code === "INTERNAL_SERVER_ERROR") {
      log.error("trpc procedure failed", {
        path: shape.data?.path,
        code: error.code,
        error: error.message,
        stack: error.stack,
      });
    }
    return shape;
  },
});

export const createRouter = t.router;
export const publicQuery = t.procedure;

/**
 * Procedures that change state, spend the AI quota or start a Lean process.
 *
 * - No reviewer token configured: the deployment is read-only (FORBIDDEN).
 * - Wrong or missing token: UNAUTHORIZED, and the failure is counted per client.
 *   A client that keeps guessing is locked out for the rest of the window, even
 *   if a later guess is right, so the lockout leaks nothing about the token.
 */
export const reviewerMutation = t.procedure.use(({ ctx, next }) => {
  if (!ctx.access.reviewEnabled) {
    throw new TRPCError({
      code: "FORBIDDEN",
      message: "This deployment is read-only: no reviewer token is configured.",
    });
  }
  if (authFailures.blocked(ctx.clientKey)) {
    throw new TRPCError({
      code: "TOO_MANY_REQUESTS",
      message: "Too many failed attempts. Try again later.",
    });
  }
  if (!ctx.access.isReviewer) {
    if (ctx.access.presentedToken) authFailures.take(ctx.clientKey);
    throw new TRPCError({ code: "UNAUTHORIZED", message: "A valid reviewer token is required." });
  }
  return next();
});
