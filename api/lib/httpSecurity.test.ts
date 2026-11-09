import { Hono } from "hono";
import { describe, expect, it } from "vitest";
import { clientKey, contentSecurityPolicy, frameAncestorsFromEnv, rateLimit, securityHeaders } from "./httpSecurity";
import { RateLimiter } from "./security";

function appWith(...middleware: Parameters<Hono["use"]>[1][]) {
  const app = new Hono();
  for (const m of middleware) app.use("*", m);
  app.get("/api/thing", (c) => c.json({ ok: true }));
  app.get("/page", (c) => c.html("<p>hi</p>"));
  return app;
}

describe("security headers", () => {
  it("are set on API and page responses", async () => {
    const app = appWith(securityHeaders());
    for (const path of ["/api/thing", "/page"]) {
      const res = await app.request(path);
      expect(res.headers.get("content-security-policy")).toContain("default-src 'self'");
      expect(res.headers.get("content-security-policy")).toContain("frame-ancestors 'none'");
      expect(res.headers.get("x-content-type-options")).toBe("nosniff");
      expect(res.headers.get("x-frame-options")).toBe("DENY");
      expect(res.headers.get("referrer-policy")).toBe("no-referrer");
    }
    expect((await app.request("/api/thing")).headers.get("cache-control")).toBe("no-store");
    expect((await app.request("/page")).headers.get("cache-control")).toBeNull();
  });

  it("allow no inline or third-party script", () => {
    const csp = contentSecurityPolicy();
    expect(csp).toContain("script-src 'self'");
    expect(csp).not.toMatch(/script-src[^;]*unsafe/);
    expect(csp).toContain("object-src 'none'");
  });

  it("framing is opt-in, per https origin", async () => {
    expect(frameAncestorsFromEnv({})).toEqual([]);
    expect(frameAncestorsFromEnv({ ALLOW_FRAMING_FROM: "https://preview.example.com, http://evil.test javascript:alert(1) *" }))
      .toEqual(["https://preview.example.com"]);
    const res = await appWith(securityHeaders({ frameAncestors: ["https://preview.example.com"] })).request("/page");
    expect(res.headers.get("content-security-policy")).toContain("frame-ancestors https://preview.example.com");
    expect(res.headers.get("x-frame-options")).toBeNull();
  });
});

describe("rate limiting", () => {
  it("answers 429 with Retry-After once a client is over its limit", async () => {
    const app = appWith(rateLimit(new RateLimiter(2, 60_000)));
    expect((await app.request("/api/thing")).status).toBe(200);
    expect((await app.request("/api/thing")).status).toBe(200);
    const blocked = await app.request("/api/thing");
    expect(blocked.status).toBe(429);
    expect(Number(blocked.headers.get("retry-after"))).toBeGreaterThan(0);
  });

  it("can exempt a path", async () => {
    const app = appWith(rateLimit(new RateLimiter(1, 60_000), (path) => path === "/page"));
    for (let i = 0; i < 5; i += 1) expect((await app.request("/page")).status).toBe(200);
  });

  it("ignores forwarding headers unless a trusted proxy is declared", async () => {
    const app = new Hono();
    const seen: string[] = [];
    app.get("/who", (c) => {
      seen.push(clientKey(c, {}), clientKey(c, { TRUST_PROXY: "1" }));
      return c.text("ok");
    });
    await app.request("/who", { headers: { "x-forwarded-for": "203.0.113.9, 10.0.0.1" } });
    expect(seen).toEqual(["unknown", "203.0.113.9"]);
  });
});
