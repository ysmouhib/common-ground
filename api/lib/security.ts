/**
 * Access control and abuse limits.
 *
 * Threat model, in one paragraph: the workspace is public to read. Three things
 * must not be available to an anonymous visitor: changing review decisions,
 * spending the site's AI quota, and starting Lean processes. All three sit behind
 * one reviewer token. With no token configured the deployment is read-only: the
 * safe state is the default, not something an operator has to remember.
 */
import { createHash, timingSafeEqual } from "node:crypto";

export const MIN_TOKEN_LENGTH = 24;

type Env = Record<string, string | undefined>;

/** The configured reviewer token, or null when review is disabled (missing or too short to be a secret). */
export function reviewerToken(env: Env = process.env): string | null {
  const token = env.REVIEWER_TOKEN?.trim() ?? "";
  return token.length >= MIN_TOKEN_LENGTH ? token : null;
}

export function bearerToken(req: Request): string | null {
  const match = /^Bearer\s+(\S+)$/i.exec(req.headers.get("authorization") ?? "");
  return match ? match[1] : null;
}

/** Constant-time comparison. Hashing first makes the two buffers the same length. */
export function tokensEqual(a: string, b: string): boolean {
  const left = createHash("sha256").update(a).digest();
  const right = createHash("sha256").update(b).digest();
  return timingSafeEqual(left, right);
}

export interface Access {
  /** A reviewer token is configured on this deployment. */
  reviewEnabled: boolean;
  /** This request carries the right token. */
  isReviewer: boolean;
  /** This request carried a token, right or wrong. */
  presentedToken: boolean;
}

export function accessFor(req: Request, env: Env = process.env): Access {
  const expected = reviewerToken(env);
  const given = bearerToken(req);
  if (!expected) return { reviewEnabled: false, isReviewer: false, presentedToken: given !== null };
  return {
    reviewEnabled: true,
    isReviewer: given !== null && tokensEqual(given, expected),
    presentedToken: given !== null,
  };
}

/** Fixed-window counter per key, with a bounded number of keys so it cannot be used to exhaust memory. */
export class RateLimiter {
  private readonly windows = new Map<string, { start: number; count: number }>();
  private readonly limit: number;
  private readonly windowMs: number;
  private readonly maxKeys: number;
  private readonly now: () => number;

  constructor(limit: number, windowMs: number, maxKeys = 5000, now: () => number = Date.now) {
    this.limit = limit;
    this.windowMs = windowMs;
    this.maxKeys = maxKeys;
    this.now = now;
  }

  private current(key: string): { start: number; count: number } | undefined {
    const entry = this.windows.get(key);
    if (entry && this.now() - entry.start >= this.windowMs) {
      this.windows.delete(key);
      return undefined;
    }
    return entry;
  }

  /** True once the key has used up its window. Does not count as a use. */
  blocked(key: string): boolean {
    const entry = this.current(key);
    return entry !== undefined && entry.count >= this.limit;
  }

  /** Count one use. Returns false when the key was already at its limit. */
  take(key: string): boolean {
    const entry = this.current(key);
    if (entry) {
      if (entry.count >= this.limit) return false;
      entry.count += 1;
      return true;
    }
    if (this.windows.size >= this.maxKeys) {
      // Drop the oldest window. Map iteration order is insertion order.
      const oldest = this.windows.keys().next().value;
      if (oldest !== undefined) this.windows.delete(oldest);
    }
    this.windows.set(key, { start: this.now(), count: 1 });
    return true;
  }

  retryAfterSeconds(key: string): number {
    const entry = this.current(key);
    if (!entry) return 0;
    return Math.max(1, Math.ceil((entry.start + this.windowMs - this.now()) / 1000));
  }
}

/** At most `slots` holders at a time. Callers that cannot get a slot are refused, not queued. */
export class Gate {
  private held = 0;
  private readonly slots: number;

  constructor(slots: number) {
    this.slots = slots;
  }

  tryEnter(): (() => void) | null {
    if (this.held >= this.slots) return null;
    this.held += 1;
    let released = false;
    return () => {
      if (released) return;
      released = true;
      this.held -= 1;
    };
  }
}

/** A count that resets each UTC day. Protects a paid quota from a leaked or over-eager token. */
export class DailyBudget {
  private day = "";
  private used = 0;
  private readonly perDay: number;
  private readonly now: () => number;

  constructor(perDay: number, now: () => number = Date.now) {
    this.perDay = perDay;
    this.now = now;
  }

  tryspend(): boolean {
    const today = new Date(this.now()).toISOString().slice(0, 10);
    if (today !== this.day) {
      this.day = today;
      this.used = 0;
    }
    if (this.used >= this.perDay) return false;
    this.used += 1;
    return true;
  }
}

function positiveInt(value: string | undefined, fallback: number): number {
  const parsed = Number.parseInt(value ?? "", 10);
  return Number.isFinite(parsed) && parsed > 0 ? parsed : fallback;
}

// Shared instances. Limits are per process; a multi-process deployment needs a shared store.
export const authFailures = new RateLimiter(10, 15 * 60_000);
export const leanGate = new Gate(1);
export const aiGate = new Gate(2);
export const aiBudget = new DailyBudget(positiveInt(process.env.AI_DAILY_LIMIT, 50));
