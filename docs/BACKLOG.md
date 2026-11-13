# Backlog: problems noticed but out of task scope, recorded here instead of being fixed (AGENTS.md, Scope fences).

- `api/proofVerifier.test.ts` "running Lean" tests create `#!/bin/sh` fake binaries and spawn them directly; on Windows `spawn` returns ENOENT, so 4 tests fail locally (39/43 pass). They pass on Linux CI. Possible fix when in scope: spawn via `sh <file>` on win32.
