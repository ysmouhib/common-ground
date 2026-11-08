# Common Ground

Common Ground is a source-grounded argument-integrity workspace. It reconstructs a public policy debate into explicit statements, lets people review the meaning of each formalization, and uses Lean 4 to check whether conclusions follow from the declared premises.

The system certifies **conditional deductions, not political truth**. Evidence, semantic review, kernel verification, and premise approval remain separate trust layers.

## Included worked example

The initial workspace reconstructs a debate about whether a city should adopt a well-designed single-use plastic bag policy. It includes:

- 15 statements owned by the advocate, critic, or shared workspace;
- five sourced evidence records with findings, excerpts, and limitations;
- four valid Lean certificates covering the advocate case, critic case, shared ground, and a conditional combined package;
- a deliberately invalid negative control that must be rejected;
- persistent human review events, verification runs, and AI interpretation drafts;
- a JSON audit export and an installable, responsive web interface.

The formalization is an editorial reconstruction, not a verbatim transcript. The facilitator-created bridge premise is labeled explicitly rather than presented as imported consensus.

## Stack

- React 19, TypeScript, Vite, Tailwind CSS, and shadcn/ui
- Hono, tRPC, Drizzle ORM, and MySQL
- Lean 4.35.0, using only the core library
- AI SDK with server-side gateway credentials
- vite-plugin-pwa for installability

## Project map

```text
api/                       Hono/tRPC API, persistence, AI, and Lean runner
contracts/lean.ts          Canonical declarations, theorem builders, and hashes
contracts/lean.test.ts     Proof-shape and certificate integrity tests
db/schema.ts               Debate, evidence, review, proof, and AI-draft tables
db/seed-data.ts            Worked-example statements and evidence
db/verification-snapshots.ts  Genuine captured Lean verification results
proofs/                    Independently inspectable generated Lean files
src/components/            Debate, proof lab, evidence, method, and review UI
public/                    Icons and other static assets
```

## Local development

Requirements: Node.js 20.12 or later and a MySQL database.

```bash
npm install
cp .env.example .env
```

Fill in the required values in `.env`, then initialize the schema and start the development server:

```bash
npm run db:push
npm run dev
```

The application uses `http://localhost:3000`. Seed data is inserted idempotently when the workspace is first loaded. Never commit `.env` or real gateway/database credentials.

### Environment variables

| Variable | Required | Purpose |
| --- | --- | --- |
| `APP_ID` | Yes | Application identifier used by the backend template |
| `APP_SECRET` | Yes | Application secret |
| `DATABASE_URL` | Yes | MySQL connection string |
| `KIMI_AGENTGW_BASE_URL` | AI only | Server-side AI gateway endpoint |
| `KIMI_AGENTGW_API_KEY` | AI only | Server-side AI gateway credential |
| `LEAN_BIN` | Live verification only | Absolute path to a Lean 4.35.0 executable |
| `PORT` | No | Production port; defaults to `3000` |

AI interpretation checks degrade gracefully when the gateway is absent or unavailable. AI drafts cannot approve premises or mutate canonical statements and proofs.

## Verification and production checks

```bash
npm run lint
npm run check
npm run test
npm run build
npm start
```

The production build writes the frontend to `dist/public` and the self-contained backend entry to `dist/boot.js`. The backend bundle must remain self-contained because production runtime files do not require `node_modules`.

A container can be built after `npm run build`:

```bash
docker build -t common-ground .
docker run --rm -p 3000:3000 common-ground
```

## Lean verification boundary

The repository includes genuine stored verification snapshots and the exact generated source hashes. It does **not** include the large Lean toolchain.

To enable live re-verification, install Lean 4.35.0 and set `LEAN_BIN` to its executable. The verifier runs Lean in an isolated temporary directory, blocks escape hatches such as `sorry` and added `axiom` declarations, hashes the exact source, and audits axiomatic dependencies.

Without a Lean executable, the application preserves stored certificates and reports live verification as unavailable; it never simulates a compiler result.

You can also inspect the worked proofs directly:

```bash
lean proofs/CommonGround.lean
lean proofs/NegativeControl.lean  # intentionally fails with a type mismatch
```

A proof certificate becomes active only when:

1. Lean accepted the exact current source;
2. the stored source hash still matches; and
3. every declared premise is currently approved.

Disputing a premise therefore suspends dependent conclusions without deleting the underlying kernel result or review history.

## Current scope and continuation notes

This is a complete single-debate prototype, not yet a multi-tenant deliberation service. Evidence import is curated, the formal model is deliberately small, and authentication is not enabled. Stored AI drafts and review decisions persist in MySQL.

Useful next engineering steps include authenticated workspaces, multiple debates, versioned statement editing, a reproducible Lean runtime image, and a reviewed evidence-import pipeline.
