# Backlog: problems noticed but out of task scope, recorded here instead of being fixed (AGENTS.md, Scope fences).

- `api/proofVerifier.test.ts` "running Lean" tests create `#!/bin/sh` fake binaries and spawn them directly; on Windows `spawn` returns ENOENT, so 4 tests fail locally (39/43 pass). They pass on Linux CI. Possible fix when in scope: spawn via `sh <file>` on win32.
- `npx drizzle-kit push` fails against MariaDB 11.8 (`serial AUTO_INCREMENT NOT NULL` parse error, ER_PARSE_ERROR 1064); it works on MySQL 8.0, which is what CI uses. Note for anyone pointing `DATABASE_URL` at a MariaDB server.
- `formalize` defaults to `max_tokens=2000`; FOLIO examples with long premise lists (all 4 above 1000 input chars) returned empty/truncated replies and failed all 3 attempts (58/204 NoFormalization overall). Re-running one with `max_tokens=4000` succeeded in 2 attempts. Consider raising the default or chunking long arguments.
