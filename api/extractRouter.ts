import { z } from "zod";

import { TRPCError } from "@trpc/server";

import { createRouter, reviewerMutation } from "./middleware";

import { aiBudget, aiGate } from "./lib/security";

import { runExtract } from "./engineRunner";

import { campName } from "./campRouter";

/**
 * Statement extraction on the same engine bridge. Spending the site's AI quota
 * sits behind the reviewer token, the per-process gate and the daily budget, like
 * the AI drafts. The provider key is the server's LLM_API_KEY — the client sends
 * only the endpoint, the model and the reply limit. A provider outage stops the
 * run and answers no_verdict; it is never scored as a wrong answer.
 */
export const extractRouter = createRouter({
  run: reviewerMutation
    .input(
      z.object({
        documents: z
          .array(z.object({ id: campName, text: z.string().min(1).max(20_000) }))
          .min(1)
          .max(10)
          .refine((docs) => new Set(docs.map((d) => d.id)).size === docs.length, "document ids must be unique"),
        baseUrl: z.string().url().max(300),
        model: z.string().min(1).max(200),
        maxTokens: z.number().int().min(50).max(100_000).default(2000),
        noJsonMode: z.boolean().default(false),
        noTemperature: z.boolean().default(false),
      }),
    )
    .mutation(async ({ input }) => {
      const release = aiGate.tryEnter();
      if (!release) {
        throw new TRPCError({ code: "TOO_MANY_REQUESTS", message: "Other AI work is running. Try again in a moment." });
      }
      try {
        if (!aiBudget.tryspend()) {
          throw new TRPCError({ code: "TOO_MANY_REQUESTS", message: "Today's AI limit for this site has been reached." });
        }
        const result = await runExtract(input);
        if (result.kind === "invalid_input") {
          throw new TRPCError({ code: "BAD_REQUEST", message: `The engine rejected the input: ${result.message}` });
        }
        return result;
      } finally {
        release();
      }
    }),
});
