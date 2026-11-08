import { ArrowDown, Bot, Braces, FileCheck2, Scale, ShieldCheck, Users } from "lucide-react";
import type { WorkspaceData } from "@/hooks/useWorkspace";
import { StatusBadge } from "./Status";
import { LEAN_TOOLCHAIN } from "@contracts/lean";

const pipeline = [
  {
    number: "01",
    title: "Import with provenance",
    icon: FileCheck2,
    text: "A public pro/con debate supplies the positions. Research and reports supply bounded findings, exact excerpts, original links, and limitations.",
  },
  {
    number: "02",
    title: "Reconstruct explicitly",
    icon: Braces,
    text: "Editors separate empirical claims, normative rules, definitions, design constraints, conclusions, and facilitator-created bridges.",
  },
  {
    number: "03",
    title: "Review the meaning",
    icon: Users,
    text: "People approve, dispute, or return a statement to draft with a mandatory note. AI can propose an alternative reading but cannot approve one.",
  },
  {
    number: "04",
    title: "Check the deduction",
    icon: ShieldCheck,
    text: `${LEAN_TOOLCHAIN} checks the exact generated source. A SHA-256 hash binds the stored result to the current theorem file.`,
  },
];

export function MethodView({ workspace }: { workspace: WorkspaceData }) {
  const recentEvents = workspace.reviewEvents.slice(0, 12);
  const recentRuns = workspace.verificationRuns.slice(0, 8);

  return (
    <div className="py-8 lg:py-10">
      <section className="grid gap-7 border-b border-[#bfc6d2] pb-9 lg:grid-cols-[1.25fr_.75fr] lg:gap-16">
        <div>
          <div className="section-label flex items-center gap-2 text-primary"><Scale className="size-4" aria-hidden="true" /> Method & trust boundaries</div>
          <h1 className="mt-2 text-4xl font-semibold tracking-[-0.035em]">Validity is checkable. Political truth is not.</h1>
          <p className="mt-3 max-w-3xl text-lg leading-relaxed text-[#4c5260]">
            Common Ground is an argument-integrity prototype. It makes a reconstruction inspectable and its deductions reproducible without turning a formal proof into a verdict about the world.
          </p>
        </div>
        <div className="border-l-4 border-primary bg-[#eaf0ff] p-5 text-sm leading-relaxed text-[#34425a]">
          <strong className="block text-base text-[#173f92]">Editorial reconstruction</strong>
          <p className="mt-2">{workspace.debate.methodNote}</p>
        </div>
      </section>

      <section aria-labelledby="pipeline-title" className="py-10">
        <div className="section-label text-primary">The pipeline</div>
        <h2 id="pipeline-title" className="mt-2 text-3xl font-semibold tracking-tight">Four layers, deliberately separated.</h2>
        <div className="mt-6 grid gap-px border border-[#c8cfdb] bg-[#c8cfdb] md:grid-cols-2 xl:grid-cols-4">
          {pipeline.map((step) => (
            <article key={step.number} className="relative min-h-64 bg-background p-5">
              <div className="flex items-center justify-between">
                <span className="font-code text-sm font-semibold text-primary">{step.number}</span>
                <step.icon className="size-5 text-primary" aria-hidden="true" />
              </div>
              <h3 className="mt-8 text-xl font-semibold leading-tight">{step.title}</h3>
              <p className="mt-3 text-sm leading-relaxed text-[#4c5260]">{step.text}</p>
            </article>
          ))}
        </div>
      </section>

      <section aria-labelledby="certificate-states" className="border-y border-[#bfc6d2] py-9">
        <div className="grid gap-7 lg:grid-cols-[.65fr_1.35fr] lg:gap-12">
          <div>
            <div className="section-label">Activation rule</div>
            <h2 id="certificate-states" className="mt-2 text-2xl font-semibold">A green badge has three necessary conditions.</h2>
            <div className="mt-5 flex flex-wrap items-center gap-2 font-code text-xs font-semibold">
              <StatusBadge tone="blue">source hash current</StatusBadge><span>+</span>
              <StatusBadge tone="blue">Lean accepted</StatusBadge><span>+</span>
              <StatusBadge tone="blue">all premises approved</StatusBadge>
            </div>
            <ArrowDown className="my-3 ml-4 size-5 text-primary" aria-hidden="true" />
            <StatusBadge tone="green" icon="shield">Active certificate</StatusBadge>
          </div>
          <dl className="grid gap-5 sm:grid-cols-2">
            <div className="border-t-2 border-primary pt-3"><dt className="font-semibold">Kernel verified · inactive</dt><dd className="mt-2 text-sm text-[#4c5260]">The deduction still checks, but at least one premise is disputed or draft. This is a suspension, not a proof failure.</dd></div>
            <div className="border-t-2 border-[#a43b2c] pt-3"><dt className="font-semibold">Lean rejected</dt><dd className="mt-2 text-sm text-[#4c5260]">The current theorem is not accepted. A deliberately invalid negative control must land here; accepting it would invalidate the test harness.</dd></div>
            <div className="border-t-2 border-[#8b93a2] pt-3"><dt className="font-semibold">Unverified or stale</dt><dd className="mt-2 text-sm text-[#4c5260]">No accepted result exists for this exact source hash. Stored output never substitutes for a current kernel check.</dd></div>
            <div className="border-t-2 border-[#8aa900] pt-3"><dt className="font-semibold">Active</dt><dd className="mt-2 text-sm text-[#4c5260]">The conditional conclusion follows from the current, approved formal premises. Evidence quality and semantic fidelity remain open to review.</dd></div>
          </dl>
        </div>
      </section>

      <section aria-labelledby="ai-boundary" className="grid gap-6 py-10 lg:grid-cols-2 lg:gap-10">
        <article className="border border-[#c8cfdb] p-6">
          <Bot className="size-6 text-primary" aria-hidden="true" />
          <div className="section-label mt-5 text-primary">AI boundary</div>
          <h2 id="ai-boundary" className="mt-2 text-2xl font-semibold">A critic, not an authority.</h2>
          <p className="mt-3 text-sm leading-relaxed text-[#4c5260]">The model receives one canonical statement and its linked evidence. It returns a proposed formal expression, a plain-language back-translation, and interpretation notes as a stored draft. It cannot write to the canonical statement, approve a premise, or activate a proof.</p>
          <p className="mt-3 text-sm leading-relaxed text-[#4c5260]">AI calls run only on the server. Quota, configuration, safety, and transient failures produce explicit degradation messages rather than invented output.</p>
        </article>
        <article className="border border-[#c8cfdb] p-6">
          <ShieldCheck className="size-6 text-primary" aria-hidden="true" />
          <div className="section-label mt-5 text-primary">Verification boundary</div>
          <h2 className="mt-2 text-2xl font-semibold">Small core, explicit assumptions.</h2>
          <p className="mt-3 text-sm leading-relaxed text-[#4c5260]">The model uses Lean’s core library only. The verifier rejects placeholder or trust-expanding commands such as <code>sorry</code>, <code>admit</code>, and added <code>axiom</code> declarations, then records compiler output and an axiom report.</p>
          <p className="mt-3 text-sm leading-relaxed text-[#4c5260]">These predicates are a deliberate formal reconstruction, not a complete theory of plastic policy. A useful negative result—rejecting litter reduction as proof of a total solution—is included in the same laboratory.</p>
          <p className="mt-3 text-sm leading-relaxed text-[#4c5260]">If a deployment has no Lean executable, genuine stored certificates remain inspectable and live re-checks report “unavailable.” The application never simulates a compiler run.</p>
        </article>
      </section>

      <section aria-labelledby="audit-trail" className="border-t border-[#bfc6d2] py-9">
        <div className="section-label text-primary">Persistent audit trail</div>
        <h2 id="audit-trail" className="mt-2 text-3xl font-semibold tracking-tight">Recent review and verification events</h2>
        <div className="mt-6 grid gap-8 lg:grid-cols-2">
          <div>
            <h3 className="section-label mb-3">Human & AI review events</h3>
            {recentEvents.length === 0 ? (
              <p className="border-y py-6 text-sm text-[#4c5260]">No review decisions or AI drafts have been recorded yet. The imported baseline remains intact.</p>
            ) : (
              <ol className="border-t">
                {recentEvents.map((event) => (
                  <li key={event.id} className="border-b py-4 text-sm">
                    <div className="flex flex-wrap items-center gap-2"><span className="font-code font-semibold text-primary">{event.statementId}</span><StatusBadge tone={event.action === "ai_draft_created" ? "blue" : "neutral"}>{event.action.replaceAll("_", " ")}</StatusBadge></div>
                    <p className="mt-2">{event.note}</p>
                    <time className="mt-1 block text-xs text-[#596373]">{event.createdAt.toLocaleString()}</time>
                  </li>
                ))}
              </ol>
            )}
          </div>
          <div>
            <h3 className="section-label mb-3">Compiler runs</h3>
            {recentRuns.length === 0 ? (
              <p className="border-y py-6 text-sm text-[#4c5260]">No runtime checks have been recorded in this deployment. Stored certificates remain inspectable in the proof laboratory.</p>
            ) : (
              <ol className="border-t">
                {recentRuns.map((run) => {
                  const proof = workspace.proofs.find((item) => item.id === run.proofId);
                  return (
                    <li key={run.id} className="border-b py-4 text-sm">
                      <div className="flex flex-wrap items-center justify-between gap-2"><span className="font-code font-semibold text-primary">{proof?.theoremName ?? run.proofId}</span><StatusBadge tone={run.outcome === "accepted" || run.outcome === "rejected" ? "green" : "amber"}>{run.outcome}</StatusBadge></div>
                      <time className="mt-1 block text-xs text-[#596373]">{run.createdAt.toLocaleString()}</time>
                      <details className="mt-2"><summary className="cursor-pointer font-semibold">Compiler output</summary><pre className="code-panel mt-2 max-h-56 overflow-auto whitespace-pre-wrap p-3">{run.output}</pre></details>
                    </li>
                  );
                })}
              </ol>
            )}
          </div>
        </div>
      </section>

      <section aria-labelledby="non-goals" className="mb-4 bg-[#1f1f1f] p-6 text-[#f8f8f8] sm:p-8">
        <div className="section-label text-[#c3ff00]">Known limits & non-goals</div>
        <h2 id="non-goals" className="mt-2 text-2xl font-semibold">What this prototype does not claim</h2>
        <ul className="mt-5 grid gap-4 text-sm leading-relaxed text-[#d7dce5] md:grid-cols-2">
          <li>It does not infer that an approved empirical premise is true, representative, or sufficient for a real policy decision.</li>
          <li>It does not discover a uniquely correct formalization of natural language; alternative encodings can change the resulting logic.</li>
          <li>It does not model utilities, probability, legislation, budgets, implementation, or every affected community.</li>
          <li>It does not treat agreement as inherently desirable. A bridge can remain disputed, and a priority disagreement can remain unresolved.</li>
        </ul>
      </section>
    </div>
  );
}
