import { createRouter, publicQuery } from "./middleware";
import { workspaceRouter } from "./workspaceRouter";
import { proofRouter } from "./proofRouter";
import { aiRouter } from "./aiRouter";
import { campRouter } from "./campRouter";
import { crosscampRouter } from "./crosscampRouter";
import { extractRouter } from "./extractRouter";

export const appRouter = createRouter({
  ping: publicQuery.query(() => ({ ok: true, ts: Date.now() })),
  workspace: workspaceRouter,
  proof: proofRouter,
  ai: aiRouter,
  camp: campRouter,
  crosscamp: crosscampRouter,
  extract: extractRouter,
});

export type AppRouter = typeof appRouter;
