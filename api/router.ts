import { createRouter, publicQuery } from "./middleware";
import { workspaceRouter } from "./workspaceRouter";
import { proofRouter } from "./proofRouter";
import { aiRouter } from "./aiRouter";
import { campRouter } from "./campRouter";

export const appRouter = createRouter({
  ping: publicQuery.query(() => ({ ok: true, ts: Date.now() })),
  workspace: workspaceRouter,
  proof: proofRouter,
  ai: aiRouter,
  camp: campRouter,
});

export type AppRouter = typeof appRouter;
