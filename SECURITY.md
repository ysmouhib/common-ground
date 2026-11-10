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
read-only.** The safe state is the default. A value that could never be sent as
a token (too short, or containing a space, which is what a container receives
from a template line with a trailing comment) counts as no token, and the server
logs which of the three states it started in.

## What enforces it

"End to end" means `e2e/run.mjs`: real HTTP requests and a real browser against the
production build with a real MySQL. CI runs it against the container image, against
a server with Lean, and against a server with no token.

| Control | Where | Unit test | End to end |
|---|---|---|---|
| Every mutation goes through `reviewerMutation`; without a token it answers 401, with no token configured 403 | `api/middleware.ts` | `api/access.test.ts` | yes |
| Constant-time token comparison | `api/lib/security.ts` | `api/lib/security.test.ts` | |
| 10 wrong tokens in a 15-minute window lock that client out until the window ends, including for the right token. A wrong token counts on every route, public queries included, so there is nowhere to test a token for free | `api/lib/security.ts`, `api/context.ts` | `api/lib/security.test.ts`, `api/access.test.ts` | yes, and that it is per client |
| 240 API requests a minute per client; 64 KB request bodies; at most 10 calls in a batch | `api/boot.ts`, `api/lib/httpSecurity.ts` | `api/lib/httpSecurity.test.ts` | yes |
| One Lean run at a time, two AI drafts at a time, a daily AI budget | `api/proofRouter.ts`, `api/aiRouter.ts` | `api/access.test.ts`, `api/lib/security.test.ts` | |
| Lean runs with an empty environment (only `PATH`), in a temporary directory, under a time limit. A run that does not finish, or a binary that does not start, is recorded as "no verdict" and leaves the stored certificate alone | `api/proofVerifier.ts` | `api/proofVerifier.test.ts` | live Lean run |
| Content-Security-Policy with no inline or third-party script, no framing, no MIME sniffing, no referrer | `api/lib/httpSecurity.ts` | `api/lib/httpSecurity.test.ts` | yes: headers, and no violation while using the page |
| The token is kept in `sessionStorage` and sent as a header, never as a cookie, so a request forged from another site carries no authority. The three encodings an HTML form can send are refused in any case | `src/lib/reviewer.ts`, `src/providers/trpc.tsx` | | yes: no cookie, nothing in `localStorage`, form posts refused even with the token |
| Encoded path traversal returns nothing from outside the public folder | static file serving | | yes |
| No secret and no `node_modules` in the container image; it runs as an unprivileged user | `Dockerfile`, `.dockerignore` | | CI checks the built image |
| Production dependencies have no known advisory (`npm audit --omit=dev`) | CI | | |
| CI runs with read-only repository permissions; every action is pinned to a commit | `.github/workflows/` | | |

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

## The model benchmark

`python -m commonground folio --mode llm|direct` sends FOLIO's sentences to the
endpoint you name. The API key is read from an environment variable, sent only as
the `Authorization` header to that endpoint, and never written to the results
(`config.json` holds the model name, the host and the request settings). Plain
`http` is refused except for localhost. The manual workflow
(`.github/workflows/model-benchmark.yml`) reads the key from a repository secret
and can be started only by someone with write access; its inputs reach the shell
as environment variables, not as script text.

## Known limits

* Limits are held in memory, per process. Several processes need a shared store,
  and a restart clears them.
* There is one reviewer role and one token. There are no accounts and no audit of
  *who* reviewed; review events record what was decided and when.
* **Who a "client" is.** By default it is the address of the TCP connection.
  Behind a reverse proxy that is the proxy, so all visitors share one bucket: the
  request limit is shared, and anyone can lock the reviewer out by sending ten
  wrong tokens every 15 minutes. That cannot unlock anything, but it denies review.
  Set `TRUST_PROXY` to the number of proxies you run in front of the app (usually
  `1`): the app then uses the address the outermost of them saw, read from the
  right-hand end of `X-Forwarded-For`, which a caller cannot forge. Setting it
  when there is no such proxy would let callers choose their own address.
* The same lockout is possible from any address the reviewer shares with others
  (an office network, a campus). It ends by itself when the window does.
* `POST /api/log` is public. It is the hosting template's sink for browser error
  reports, and it is what lets a page error show up in the server log. It accepts
  64 KB per request and 50 lines per request, writes at most 3000 lines a minute
  in total to a file capped at 8 MiB, scrubs credential-looking values and never
  sends anything back. Its per-client cap trusts forwarding headers, so only the
  total cap is a real bound: someone can fill that log with noise.
* The app does not send `Strict-Transport-Security`; it does not know whether it
  is behind TLS. Set it where TLS ends.
* `Dockerfile.platform` is the original hosting recipe and copies `.env` into the
  image. It is kept for that platform only; see the warning at its top.
* Development tooling (`drizzle-kit`, `typescript-eslint`, the Vite dev server,
  `vite-plugin-pwa`) has open advisories, 16 moderate and 2 low on 10 November
  2026, whose fixes are breaking upgrades. None of it is in the production bundle.

## Reporting a problem

Open a private security advisory on the repository, or write to the address on the
maintainer's GitHub profile. Please do not open a public issue for a vulnerability.
