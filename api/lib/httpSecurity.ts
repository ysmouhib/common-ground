/**
 * HTTP-level protections, kept apart from boot.ts so they can be tested on a bare app.
 */
import type { Context, MiddlewareHandler } from "hono";
import { RateLimiter } from "./security";

/** How many reverse proxies the operator runs in front of the app (TRUST_PROXY=n); 0 when none is declared. */
export function trustedProxyHops(env: Record<string, string | undefined> = process.env): number {
  const hops = Number.parseInt(env.TRUST_PROXY ?? "", 10);
  return Number.isInteger(hops) && hops >= 1 && hops <= 10 ? hops : 0;
}

/**
 * Who is calling, for rate limits and the token lockout. The socket address by
 * default. X-Forwarded-For is written by the caller except for the entries that
 * the operator's own proxies append, so it is read only when TRUST_PROXY=n declares
 * n such proxies, and then only the n-th entry from the right: the address the
 * outermost trusted proxy saw. Everything to its left is the caller's own text.
 */
export function clientKey(c: Context, env: Record<string, string | undefined> = process.env): string {
  const hops = trustedProxyHops(env);
  if (hops > 0) {
    const chain = (c.req.header("x-forwarded-for") ?? "")
      .split(",")
      .map((entry) => entry.trim())
      .filter(Boolean);
    const entry = chain[chain.length - hops];
    if (entry) return entry.slice(0, 64);
  }
  const incoming = (c.env as { incoming?: { socket?: { remoteAddress?: string } } } | undefined)?.incoming;
  return incoming?.socket?.remoteAddress ?? "unknown";
}

export function rateLimit(limiter: RateLimiter, skip: (path: string) => boolean = () => false): MiddlewareHandler {
  return async (c, next) => {
    if (skip(c.req.path)) return next();
    const key = clientKey(c);
    if (!limiter.take(key)) {
      c.header("Retry-After", String(limiter.retryAfterSeconds(key)));
      return c.json({ error: "Too many requests" }, 429);
    }
    return next();
  };
}

export interface HeaderOptions {
  /** Origins allowed to embed the app in a frame, e.g. a hosting platform's preview. Empty: none. */
  frameAncestors?: string[];
}

export function contentSecurityPolicy(options: HeaderOptions = {}): string {
  const ancestors = options.frameAncestors?.length ? options.frameAncestors.join(" ") : "'none'";
  return [
    "default-src 'self'",
    "script-src 'self'",
    // React sets inline style attributes; no inline <style> or external stylesheet is allowed.
    "style-src 'self' 'unsafe-inline'",
    "img-src 'self' data:",
    "font-src 'self' data:",
    "connect-src 'self'",
    "worker-src 'self'",
    "manifest-src 'self'",
    "object-src 'none'",
    "base-uri 'self'",
    "form-action 'self'",
    `frame-ancestors ${ancestors}`,
  ].join("; ");
}

/** Response headers for production. Set after the handler so they also cover raw tRPC responses. */
export function securityHeaders(options: HeaderOptions = {}): MiddlewareHandler {
  const csp = contentSecurityPolicy(options);
  return async (c, next) => {
    await next();
    const h = c.res.headers;
    h.set("Content-Security-Policy", csp);
    h.set("X-Content-Type-Options", "nosniff");
    h.set("Referrer-Policy", "no-referrer");
    h.set("Cross-Origin-Opener-Policy", "same-origin");
    h.set("Permissions-Policy", "camera=(), microphone=(), geolocation=(), payment=()");
    if (!options.frameAncestors?.length) h.set("X-Frame-Options", "DENY");
    if (c.req.path.startsWith("/api/")) h.set("Cache-Control", "no-store");
  };
}

export function frameAncestorsFromEnv(env: Record<string, string | undefined> = process.env): string[] {
  return (env.ALLOW_FRAMING_FROM ?? "")
    .split(/[\s,]+/)
    .filter((origin) => /^https:\/\/[A-Za-z0-9.*-]+(:\d+)?$/.test(origin));
}
