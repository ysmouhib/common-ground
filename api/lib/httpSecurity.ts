/**
 * HTTP-level protections, kept apart from boot.ts so they can be tested on a bare app.
 */
import type { Context, MiddlewareHandler } from "hono";
import { RateLimiter } from "./security";

/**
 * Who is calling, for rate limiting. The socket address by default. Forwarding
 * headers are client-controlled unless a trusted proxy sets them, so they are used
 * only when TRUST_PROXY=1 says such a proxy is in front.
 */
export function clientKey(c: Context, env: Record<string, string | undefined> = process.env): string {
  if (env.TRUST_PROXY === "1") {
    const forwarded = c.req.header("x-forwarded-for")?.split(",")[0]?.trim();
    if (forwarded) return forwarded.slice(0, 64);
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
