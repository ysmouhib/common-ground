# Security

## What is protected

The workspace is public to read. Three things are not available to an anonymous
visitor, because each costs something or changes the record:

| Action | Why it is restricted |
|---|---|
| Recording a review decision (approve / dispute a premise) | It changes which conclusions the site presents as certified. |
| Requesting an AI interpretation draft | It spends the site's AI quota. |
| Re-running Lean | It starts a process on the server. |

All three require the reviewer token (`REVIEWER_TOKEN`, at least 24 characters),
sent as `Authorization: Bearer …`. **With no token configured the deployment is
read-only.** The safe state is the default.

## What enforces it

| Control | Where | Test |
|---|---|---|
| Every mutation goes through `reviewerMutation` | `api/middleware.ts` | `api/access.test.ts` |
| Constant-time token comparison; 10 wrong tokens lock a client out for 15 minutes, including for the right token | `api/lib/security.ts` | `api/lib/security.test.ts`, `api/access.test.ts` |
| 240 API requests a minute per client; 64 KB request bodies; at most 10 calls in a batch | `api/boot.ts`, `api/lib/httpSecurity.ts` | `api/lib/httpSecurity.test.ts` |
| One Lean run at a time, two AI drafts at a time, a daily AI budget | `api/proofRouter.ts`, `api/aiRouter.ts` | `api/access.test.ts`, `api/lib/security.test.ts` |
| Content-Security-Policy with no inline or third-party script, no framing, no MIME sniffing, no referrer | `api/lib/httpSecurity.ts` | `api/lib/httpSecurity.test.ts` |
| The token is kept in `sessionStorage` and sent as a header, never as a cookie, so a request forged from another site carries no authority | `src/lib/reviewer.ts`, `src/providers/trpc.tsx` | — |
| No secret in the container image | `Dockerfile`, `.dockerignore` | — |
| Production dependencies have no known advisory (`npm audit --omit=dev`) | CI | CI |

## Untrusted text

* **Lean executes code while it checks a file.** No text written by a visitor or a
  language model is ever passed to Lean. The web app compiles five fixed sources.
  The engine generates Lean from a syntax tree after renaming every symbol, and
  refuses to run a source containing any token outside its own vocabulary
  (`engine/commonground/lean.py`, `engine/tests/test_lean.py`).
* **Language models are given statements as data.** The text is passed as a JSON
  value with an instruction not to follow anything inside it. A model's reply can
  only become a stored draft (web app) or a formula that parses in a small grammar
  (engine). It cannot change a statement, a proof or a review decision.
* **Everything a visitor can write is rendered as text** by React; nothing is
  inserted as HTML.

## Known limits

* Limits are held in memory, per process. Several processes need a shared store.
* There is one reviewer role and one token. There are no accounts and no audit of
  *who* reviewed; review events record what was decided and when.
* Behind a reverse proxy, set `TRUST_PROXY=1` only if the proxy overwrites
  `X-Forwarded-For`; otherwise all clients share one rate-limit bucket (safe, but
  coarse).
* `Dockerfile.platform` is the original hosting recipe and copies `.env` into the
  image. It is kept for that platform only; see the warning at its top.
* Development tooling (`drizzle-kit`, `eslint`, the Vite dev server) has open
  advisories that need breaking upgrades. None of it is in the production bundle.

## Reporting a problem

Open a private security advisory on the repository, or write to the address on the
maintainer's GitHub profile. Please do not open a public issue for a vulnerability.
