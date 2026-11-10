import { describe, expect, it } from "vitest";
import { accessFor, bearerToken, DailyBudget, Gate, MIN_TOKEN_LENGTH, RateLimiter, reviewerToken, reviewSetting, tokensEqual } from "./security";

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

  it("is disabled when the value could never be sent as a token", () => {
    // What `docker run --env-file` passes for a template line with a trailing comment.
    const literal = "           # At least 24 characters. Treat it like a password.";
    expect(reviewerToken({ REVIEWER_TOKEN: literal })).toBeNull();
    expect(reviewerToken({ REVIEWER_TOKEN: `${TOKEN} ${TOKEN}` })).toBeNull();
    expect(accessFor(request("Bearer #"), "c", { REVIEWER_TOKEN: literal }, new RateLimiter(10, 60_000)).reviewEnabled).toBe(false);
  });

  it("says at start-up which of the three states the deployment is in, without the token", () => {
    expect(reviewSetting({}).note).toBe("read-only: no REVIEWER_TOKEN is set");
    expect(reviewSetting({ REVIEWER_TOKEN: "short" }).note).toMatch(/^read-only: REVIEWER_TOKEN is set but cannot be used/);
    const enabled = reviewSetting({ REVIEWER_TOKEN: TOKEN });
    expect(enabled.note).toBe("review enabled: a reviewer token is configured");
    expect(enabled.note).not.toContain(TOKEN);
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
  const fresh = () => new RateLimiter(10, 15 * 60_000);

  it("is read-only when no token is configured, whatever the request carries", () => {
    expect(accessFor(request(`Bearer ${TOKEN}`), "c", {}, fresh()))
      .toEqual({ reviewEnabled: false, isReviewer: false, presentedToken: true, lockedOut: false });
    expect(accessFor(request(), "c", {}, fresh()))
      .toEqual({ reviewEnabled: false, isReviewer: false, presentedToken: false, lockedOut: false });
  });

  it("grants review only to the exact token", () => {
    const env = { REVIEWER_TOKEN: TOKEN };
    expect(accessFor(request(`Bearer ${TOKEN}`), "c", env, fresh()).isReviewer).toBe(true);
    expect(accessFor(request(`Bearer ${TOKEN}x`), "c", env, fresh()))
      .toEqual({ reviewEnabled: true, isReviewer: false, presentedToken: true, lockedOut: false });
    expect(accessFor(request(), "c", env, fresh()))
      .toEqual({ reviewEnabled: true, isReviewer: false, presentedToken: false, lockedOut: false });
  });

  it("locks a client out after ten wrong tokens, and then refuses the right one too", () => {
    const env = { REVIEWER_TOKEN: TOKEN };
    const failures = fresh();
    for (let i = 0; i < 10; i += 1) {
      expect(accessFor(request(`Bearer guess-${i}`), "guesser", env, failures).lockedOut).toBe(false);
    }
    expect(accessFor(request(`Bearer ${TOKEN}`), "guesser", env, failures))
      .toEqual({ reviewEnabled: true, isReviewer: false, presentedToken: true, lockedOut: true });
    // Other clients are unaffected, and requests without a token never count.
    expect(accessFor(request(`Bearer ${TOKEN}`), "someone-else", env, failures).isReviewer).toBe(true);
    const quiet = fresh();
    for (let i = 0; i < 50; i += 1) accessFor(request(), "reader", env, quiet);
    expect(accessFor(request(`Bearer ${TOKEN}`), "reader", env, quiet).isReviewer).toBe(true);
  });

  it("a right token does not reset or extend a lockout window", () => {
    let now = 0;
    const failures = new RateLimiter(10, 15 * 60_000, 100, () => now);
    const env = { REVIEWER_TOKEN: TOKEN };
    for (let i = 0; i < 10; i += 1) accessFor(request("Bearer wrong"), "c", env, failures);
    expect(accessFor(request(`Bearer ${TOKEN}`), "c", env, failures).lockedOut).toBe(true);
    now = 15 * 60_000;
    expect(accessFor(request(`Bearer ${TOKEN}`), "c", env, failures))
      .toEqual({ reviewEnabled: true, isReviewer: true, presentedToken: true, lockedOut: false });
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
