import { describe, expect, it } from "vitest";
import { accessFor, bearerToken, DailyBudget, Gate, MIN_TOKEN_LENGTH, RateLimiter, reviewerToken, tokensEqual } from "./security";

const TOKEN = "a-long-random-reviewer-token-0123456789";
const request = (authorization?: string) =>
  new Request("http://localhost/api/trpc/x", { headers: authorization ? { authorization } : {} });

describe("reviewer token", () => {
  it("is disabled when missing or too short to be a secret", () => {
    expect(reviewerToken({})).toBeNull();
    expect(reviewerToken({ REVIEWER_TOKEN: "short" })).toBeNull();
    expect(reviewerToken({ REVIEWER_TOKEN: "x".repeat(MIN_TOKEN_LENGTH - 1) })).toBeNull();
    expect(reviewerToken({ REVIEWER_TOKEN: `  ${TOKEN}  ` })).toBe(TOKEN);
  });

  it("is read only from a well-formed Bearer header", () => {
    expect(bearerToken(request(`Bearer ${TOKEN}`))).toBe(TOKEN);
    expect(bearerToken(request(`bearer ${TOKEN}`))).toBe(TOKEN);
    expect(bearerToken(request(TOKEN))).toBeNull();
    expect(bearerToken(request(`Basic ${TOKEN}`))).toBeNull();
    expect(bearerToken(request())).toBeNull();
  });

  it("compares whole values", () => {
    expect(tokensEqual(TOKEN, TOKEN)).toBe(true);
    expect(tokensEqual(TOKEN, TOKEN.slice(0, -1))).toBe(false);
    expect(tokensEqual(TOKEN, `${TOKEN}x`)).toBe(false);
    expect(tokensEqual("", TOKEN)).toBe(false);
  });
});

describe("access", () => {
  it("is read-only when no token is configured, whatever the request carries", () => {
    expect(accessFor(request(`Bearer ${TOKEN}`), {})).toEqual({ reviewEnabled: false, isReviewer: false, presentedToken: true });
    expect(accessFor(request(), {})).toEqual({ reviewEnabled: false, isReviewer: false, presentedToken: false });
  });

  it("grants review only to the exact token", () => {
    const env = { REVIEWER_TOKEN: TOKEN };
    expect(accessFor(request(`Bearer ${TOKEN}`), env).isReviewer).toBe(true);
    expect(accessFor(request(`Bearer ${TOKEN}x`), env)).toEqual({ reviewEnabled: true, isReviewer: false, presentedToken: true });
    expect(accessFor(request(), env)).toEqual({ reviewEnabled: true, isReviewer: false, presentedToken: false });
  });
});

describe("limits", () => {
  it("rate limiter blocks at the limit and recovers after the window", () => {
    let now = 1_000;
    const limiter = new RateLimiter(3, 10_000, 100, () => now);
    expect([1, 2, 3].map(() => limiter.take("a"))).toEqual([true, true, true]);
    expect(limiter.take("a")).toBe(false);
    expect(limiter.blocked("a")).toBe(true);
    expect(limiter.take("b")).toBe(true); // keys are independent
    expect(limiter.retryAfterSeconds("a")).toBe(10);
    now += 10_000;
    expect(limiter.blocked("a")).toBe(false);
    expect(limiter.take("a")).toBe(true);
  });

  it("rate limiter keeps a bounded number of keys", () => {
    const limiter = new RateLimiter(1, 60_000, 3, () => 0);
    for (const key of ["a", "b", "c", "d", "e"]) limiter.take(key);
    expect(limiter.blocked("e")).toBe(true);
    expect(limiter.blocked("a")).toBe(false); // evicted, oldest first
  });

  it("gate refuses a caller when all slots are held and frees a slot exactly once", () => {
    const gate = new Gate(1);
    const release = gate.tryEnter();
    expect(release).not.toBeNull();
    expect(gate.tryEnter()).toBeNull();
    release!();
    release!(); // a second release must not free a slot that someone else now holds
    const next = gate.tryEnter();
    expect(next).not.toBeNull();
    expect(gate.tryEnter()).toBeNull();
  });

  it("daily budget resets with the UTC day", () => {
    let now = Date.UTC(2026, 10, 9, 23, 59);
    const budget = new DailyBudget(2, () => now);
    expect([budget.tryspend(), budget.tryspend(), budget.tryspend()]).toEqual([true, true, false]);
    now = Date.UTC(2026, 10, 10, 0, 1);
    expect(budget.tryspend()).toBe(true);
  });
});
