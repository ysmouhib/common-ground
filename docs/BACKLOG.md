# Backlog: problems noticed but out of task scope, recorded here instead of being fixed (AGENTS.md, Scope fences).

- `api/proofVerifier.test.ts` "running Lean" tests create `#!/bin/sh` fake binaries and spawn them directly; on Windows `spawn` returns ENOENT, so 4 tests fail locally (39/43 pass). They pass on Linux CI. Possible fix when in scope: spawn via `sh <file>` on win32.
- `npx drizzle-kit push` fails against MariaDB 11.8 (`serial AUTO_INCREMENT NOT NULL` parse error, ER_PARSE_ERROR 1064); it works on MySQL 8.0, which is what CI uses. Note for anyone pointing `DATABASE_URL` at a MariaDB server.
- `bench.mcnemar_exact` results are rounded to 6 decimals in `compare`/`report`, so a very small p (e.g. 1.8e-08 for 52 vs 9 discordant) prints as "p = 0.". Display-only; the raw value is not 0.
