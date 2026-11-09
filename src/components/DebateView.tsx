import { ArrowRight, ArrowUpRight, BookOpen, CheckCircle2, GitBranch, Scale, ShieldCheck } from "lucide-react";
import type { Statement, WorkspaceData } from "@/hooks/useWorkspace";
import { ApprovalBadge, ProofBadge, StatusBadge } from "./Status";

interface Props {
  workspace: WorkspaceData;
  onOpenStatement: (id: string) => void;
  onOpenProof: (id: string) => void;
}

function StatementRow({ statement, onOpen }: { statement: Statement; onOpen: () => void }) {
  return (
    <button
      type="button"
      onClick={onOpen}
      className="transition-ui group flex min-h-16 w-full items-start gap-3 border-b border-[#d5d9df] py-3 text-left last:border-b-0 hover:bg-secondary"
    >
      <span className="mt-0.5 w-7 shrink-0 font-code text-xs font-semibold text-primary">{statement.id}</span>
      <span className="min-w-0 flex-1">
        <span className="block font-medium leading-snug group-hover:underline group-hover:underline-offset-4">{statement.title}</span>
        <span className="mt-1 block text-sm leading-snug text-[#4c5260]">{statement.body}</span>
      </span>
      <ApprovalBadge status={statement.approvalStatus} />
    </button>
  );
}

export function DebateView({ workspace, onOpenStatement, onOpenProof }: Props) {
  const { debate, statements, proofs, analysis } = workspace;
  const advocate = statements.filter((statement) => statement.owner === "advocate" && statement.kind !== "conclusion");
  const critic = statements.filter((statement) => statement.owner === "critic" && statement.kind !== "conclusion");
  const shared = statements.filter((statement) => statement.owner === "shared" && statement.kind !== "conclusion");
  const mainProofs = proofs.filter((proof) => !proof.isNegativeControl);

  return (
    <div>
      <section className="grid gap-8 border-b border-[#bfc6d2] py-10 lg:grid-cols-[1.45fr_.55fr] lg:gap-16 lg:py-14">
        <div>
          <div className="section-label flex items-center gap-2 text-primary">
            <Scale className="size-4" aria-hidden="true" /> Imported public debate · formal reconstruction
          </div>
          <h1 className="mt-4 max-w-4xl text-4xl font-semibold leading-[1.08] tracking-[-0.04em] sm:text-5xl lg:text-6xl">
            {debate.question}
          </h1>
          <p className="mt-6 max-w-3xl text-lg leading-relaxed text-[#444]">{debate.summary}</p>
          <a
            href={debate.sourceUrl}
            target="_blank"
            rel="noreferrer"
            className="mt-5 inline-flex min-h-11 items-center gap-2 font-semibold text-primary underline underline-offset-4"
          >
            Open the source debate <ArrowUpRight className="size-4" aria-hidden="true" />
          </a>
        </div>
        <aside className="border-t-4 border-primary bg-[#eaf0ff] p-5 lg:mt-3">
          <h2 className="text-lg font-semibold">The guarantee has a boundary.</h2>
          <dl className="mt-4 space-y-4 text-sm">
            <div>
              <dt className="font-semibold text-primary">Lean certifies</dt>
              <dd className="mt-1 text-[#3d495d]">A conclusion follows from the exact formal premises shown.</dd>
            </div>
            <div>
              <dt className="font-semibold text-primary">Lean does not certify</dt>
              <dd className="mt-1 text-[#3d495d]">That a source is correct, a value is right, or AI preserved the speaker’s meaning.</dd>
            </div>
          </dl>
        </aside>
      </section>

      <section aria-label="Workspace totals" className="grid grid-cols-2 border-b border-[#bfc6d2] md:grid-cols-4">
        {[
          { label: "Approved statements", value: analysis.approvedCount, icon: CheckCircle2 },
          { label: "Active certificates", value: analysis.activeProofCount, icon: ShieldCheck },
          { label: "Evidence records", value: workspace.evidence.length, icon: BookOpen },
          { label: "Open disputes", value: analysis.disputedCount, icon: GitBranch },
        ].map((item) => (
          <div key={item.label} className="border-r border-[#d5d9df] px-4 py-5 last:border-r-0 md:px-6">
            <item.icon className="size-5 text-primary" aria-hidden="true" />
            <div className="mt-2 font-display text-3xl font-semibold tracking-tight">{item.value}</div>
            <div className="text-sm text-[#4c5260]">{item.label}</div>
          </div>
        ))}
      </section>

      <section aria-labelledby="positions-title" className="py-10">
        <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-end">
          <div>
            <div className="section-label text-primary">Two positions · explicit premises</div>
            <h2 id="positions-title" className="mt-2 text-3xl font-semibold tracking-tight">Put the reasoning on the table.</h2>
          </div>
          <p className="max-w-md text-sm text-[#4c5260]">Select any statement to inspect its source, formal reading, review status, and dependent proofs.</p>
        </div>

        <div className="mt-7 grid gap-8 lg:grid-cols-2 lg:gap-10">
          <article>
            <div className="border-t-4 border-primary pb-4 pt-4">
              <div className="section-label text-primary">Position A</div>
              <h3 className="mt-1 text-xl font-semibold">Targeted-policy advocate</h3>
              <p className="mt-1 text-sm text-[#4c5260]">“A well-designed bag policy is a measurable pollution-reduction tool.”</p>
            </div>
            <div>
              {advocate.map((statement) => (
                <StatementRow key={statement.id} statement={statement} onOpen={() => onOpenStatement(statement.id)} />
              ))}
            </div>
          </article>
          <article>
            <div className="border-t-4 border-[#b37b00] pb-4 pt-4">
              <div className="section-label text-[#694b00]">Position B</div>
              <h3 className="mt-1 text-xl font-semibold">Upstream-first critic</h3>
              <p className="mt-1 text-sm text-[#4c5260]">“Do not mistake a consumer-side improvement for a complete plastics policy.”</p>
            </div>
            <div>
              {critic.map((statement) => (
                <StatementRow key={statement.id} statement={statement} onOpen={() => onOpenStatement(statement.id)} />
              ))}
            </div>
          </article>
        </div>
      </section>

      <section aria-labelledby="shared-premises" className="border-y border-[#bfc6d2] py-8">
        <div className="grid gap-6 lg:grid-cols-[.55fr_1.45fr] lg:gap-12">
          <div>
            <div className="section-label">Shared & facilitator statements</div>
            <h2 id="shared-premises" className="mt-2 text-2xl font-semibold">The bridge is visible.</h2>
            <p className="mt-2 text-sm text-[#4c5260]">B1 is deliberately marked as workshop-created. It is not smuggled in as sourced evidence.</p>
          </div>
          <div>
            {shared.map((statement) => (
              <StatementRow key={statement.id} statement={statement} onOpen={() => onOpenStatement(statement.id)} />
            ))}
          </div>
        </div>
      </section>

      <section aria-labelledby="conclusions-title" className="py-10">
        <div className="section-label text-primary">Live conclusion board</div>
        <h2 id="conclusions-title" className="mt-2 text-3xl font-semibold tracking-tight">What follows right now?</h2>
        <p className="mt-2 max-w-2xl text-[#4c5260]">
          A certificate is active only when its current Lean source hash is verified and every listed premise is approved.
        </p>
        <div className="mt-6 grid border-y border-[#bfc6d2] md:grid-cols-2">
          {mainProofs.map((proof) => {
            const conclusion = statements.find((statement) => statement.id === proof.conclusionId);
            return (
              <button
                type="button"
                key={proof.id}
                onClick={() => onOpenProof(proof.id)}
                className="transition-ui group flex min-h-48 flex-col items-start border-b border-r border-[#d5d9df] p-5 text-left last:border-b-0 hover:bg-secondary md:[&:nth-last-child(-n+2)]:border-b-0"
              >
                <div className="flex w-full items-center justify-between gap-3">
                  <span className="font-code text-xs font-semibold text-primary">{proof.theoremName}</span>
                  <ProofBadge proof={proof} />
                </div>
                <span className="mt-4 text-lg font-semibold leading-snug group-hover:underline group-hover:underline-offset-4">{conclusion?.body}</span>
                <span className="mt-auto inline-flex items-center gap-2 pt-4 text-sm font-semibold text-primary">
                  Inspect deduction <ArrowRight className="size-4" aria-hidden="true" />
                </span>
              </button>
            );
          })}
        </div>
      </section>

      {analysis.combinedActive && (
        <section className="mb-10 border border-[#8aa900] bg-accent p-6 text-accent-foreground sm:p-8">
          <div className="section-label">Common ground found · conditional on B1</div>
          <h2 className="mt-2 max-w-4xl text-2xl font-semibold leading-tight sm:text-3xl">
            Consider a combined package: a responsible targeted bag policy and upstream production caps.
          </h2>
          <p className="mt-3 max-w-3xl text-[#314300]">
            This is not a compromise invented by AI. It is a Lean-checked deduction from both cases plus the explicit facilitator bridge.
          </p>
          <button
            type="button"
            onClick={() => onOpenProof("proof-combined")}
            className="transition-ui mt-5 inline-flex min-h-11 items-center gap-2 bg-[#1f1f1f] px-4 font-semibold text-[#f8f8f8] hover:bg-[#363636]"
          >
            Open the common-ground proof <ArrowRight className="size-4" aria-hidden="true" />
          </button>
        </section>
      )}

      <section aria-labelledby="disagreement-title" className="pb-12">
        <div className="section-label">Disagreement diagnosis</div>
        <h2 id="disagreement-title" className="mt-2 text-2xl font-semibold">
          {analysis.positionsCompatible ? "A priority dispute, not a direct contradiction." : "The two positions contradict each other."}
        </h2>
        <p className="mt-2 max-w-3xl text-sm text-[#4c5260]">
          {analysis.positionsCompatible
            ? "Computed, not asserted: a solver found one model in which every premise of both positions holds, and an independent checker confirmed it. So neither side is logically forced to reject the other's premises."
            : `Computed, not asserted: the premises cannot all hold together. The solver found ${analysis.conflicts.length} minimal conflict(s); the smallest ways out are listed in the audit export.`}
        </p>
        <div className="mt-5 grid gap-px border border-[#c8cfdb] bg-[#c8cfdb] md:grid-cols-3">
          {[
            { id: "A2", label: "Empirical scope", text: "How much litter reduction is enough, and how far does the evidence generalize?" },
            { id: "A4", label: "Normative priority", text: "Should measured local benefits trigger adoption, or should upstream root causes take priority?" },
            { id: "C3", label: "Design constraints", text: "Are access, actual reuse, and substitute life-cycle impacts adequately addressed?" },
          ].map((item) => (
            <button
              type="button"
              key={item.id}
              onClick={() => onOpenStatement(item.id)}
              className="transition-ui min-h-44 bg-background p-5 text-left hover:bg-secondary"
            >
              <StatusBadge tone="blue">{item.id}</StatusBadge>
              <h3 className="mt-3 font-semibold">{item.label}</h3>
              <p className="mt-2 text-sm text-[#4c5260]">{item.text}</p>
            </button>
          ))}
        </div>
      </section>
    </div>
  );
}
