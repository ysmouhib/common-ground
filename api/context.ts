import type { FetchCreateContextFnOptions } from "@trpc/server/adapters/fetch";
import { accessFor, type Access } from "./lib/security";

export type TrpcContext = {
  req: Request;
  resHeaders: Headers;
  /** What this request may do; decided once per request (see lib/security.ts). */
  access: Access;
  /** Who is calling, for rate limits (see lib/httpSecurity.ts). */
  clientKey: string;
};

export function contextFor(clientKey: string) {
  return async (opts: FetchCreateContextFnOptions): Promise<TrpcContext> => ({
    req: opts.req,
    resHeaders: opts.resHeaders,
    access: accessFor(opts.req, clientKey),
    clientKey,
  });
}
