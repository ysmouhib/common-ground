import { useState } from "react";

import { Bot, Check, ClipboardCheck, ListChecks, MessageSquareWarning, Play } from "lucide-react";

import type { inferProcedureInput } from "@trpc/server";

import type { AppRouter } from "../../api/router";

import { allDecided, approvedCandidatesJson, useAxiomQueue } from "@/hooks/useAxiomQueue";

import type { CampReport } from "@contracts/engineReport";

import type { WorkspaceData } from "@/hooks/useWorkspace";

import { trpc } from "@/providers/trpc";

import { StatusBadge } from "./Status";

type CampRunInput = inferProcedureInput<AppRouter["camp"]["run"]>;

function provenanceLine(source: CampReport["source"]): string {
  const s = source as Record<string, unknown>;
  const parts: string[] = [`model ${String(s.model)}`];
  if (s.host !== undefined) parts.push(`host ${String(s.host)}`);
  if (s.temperature !== undefined) parts.push(`temperature ${String(s.temperature)}`);
  if (s.json_mode !== undefined) parts.push(`json_mode ${String(s.json_mode)}`);
  if (s.max_tokens !== undefined) parts.push(`max_tokens ${String(s.max_tokens)}`);
  if (typeof s.prompt_sha256 === "string") parts.push(`prompt sha256 ${s.prompt_sha256.slice(0, 12)}…`);
  return parts.join(" · ");
}

function ExistenceBadge({ report }: { report: CampReport }) {
  const existence = report.existence;
  if (existence.status === "certified") {
    return <StatusBadge tone="green" icon="check">Existence: certified — a verified sufficient system was found</StatusBadge>;
  }
  if (existence.status === "none") {
    return (
      <StatusBadge tone="red" icon="warning">
        Existence: none — {existence.reason ?? ""}{existence.detail ? ` (${existence.detail})` : ""}
      </StatusBadge>
    );
  }
  return (
    <StatusBadge tone="amber" icon="draft">
      Existence: pending — {existence.reason ?? "no verdict"}{existence.detail ? ` (${existence.detail})` : ""}
    </StatusBadge>
  );
}

function SystemCard({ report, index }: { report: CampReport; index: number }) {
  const system = report.systems[index];
  if (!system) return null;
  const checks = [
    system.checks.consistent,
    ...system.checks.sufficiency,
    ...system.checks.firm_rejections,
    ...system.checks.soft_rejections,
    ...system.checks.minimality,
  ];
  return (
    <details className="border border-[#c8cfdb] bg-background p-4">
      <summary className="flex min-h-7 cursor-pointer flex-wrap items-center gap-2">
        <span className="font-semibold">System {index + 1}</span>
        <StatusBadge tone={system.certified ? "green" : "neutral"}>{system.badge}</StatusBadge>
        <span className="text-sm text-[#4c5260]">cost {system.cost.toFixed(4)} · {system.axioms.length} axiom(s)</span>
      </summary>
      <ul className="mt-3 space-y-1 text-sm">
        {system.axioms.map((axiom) => (
          <li key={axiom}><code className="code-panel block whitespace-pre-wrap break-words p-2">{axiom}</code></li>
        ))}
      </ul>
      <ul className="mt-3 space-y-1 border-t pt-3 text-sm">
        {checks.map((check, i) => (
          <li key={i} className="flex flex-wrap gap-2">
            <StatusBadge tone={check.outcome === "holds" ? "green" : check.outcome === "fails" ? "red" : "amber"}>
              {check.outcome}
            </StatusBadge>
            <span className="font-code text-xs">{check.kind}</span>
            <code className="font-code text-xs">{check.claim}</code>
            <span className="text-[#4c5260]">{check.badge}</span>
            <span className="w-full text-xs text-[#4c5260]">{check.detail}</span>
          </li>
        ))}
      </ul>
    </details>
  );
}

export function AxiomQueueView({ workspace }: { workspace: WorkspaceData }) {
  const [recordText, setRecordText] = useState("");
  const [candidatesText, setCandidatesText] = useState('{"candidates": []}');
  const [lam, setLam] = useState(0.3);
  const [maxChecks, setMaxChecks] = useState(4000);
  const [lean, setLean] = useState(false);
  const [inputError, setInputError] = useState("");
  const [copied, setCopied] = useState(false);
  const [notes, setNotes] = useState<Record<string, string>>({});
  const queue = useAxiomQueue();

  const run = trpc.camp.run.useMutation({
    onError: (error) => setInputError(error.message),
  });
  const report = run.data?.kind === "report" ? run.data.report : undefined;
  const allReviewed = report ? allDecided(report, queue.decisions) : false;

  function runReport() {
    setInputError("");
    let record: CampRunInput["record"];
    let candidates: CampRunInput["candidates"];
    try {
      record = JSON.parse(recordText) as CampRunInput["record"];
      candidates = JSON.parse(candidatesText) as CampRunInput["candidates"];
    } catch {
      setInputError("The record and candidates fields must be valid JSON (copy the record from the Camps view).");
      return;
    }
    run.mutate({ record, candidates, lam, maxChecks, timeoutMs: 5000, lean });
  }

  function copyApproved() {
    if (!report) return;
    void navigator.clipboard.writeText(JSON.stringify(approvedCandidatesJson(report, queue.decisions), null, 2));
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }

  const canReview = workspace.access.isReviewer;

  return (
    <div className="py-8">
      <header className="max-w-3xl">
        <h1 className="text-3xl font-semibold tracking-[-0.02em]">Axiom review queue</h1>
        <p className="mt-3 text-sm leading-relaxed text-[#4c5260]">
          Run a camp report, then approve or reject each proposed axiom with a note. A model proposes; a human
          decides — no model output reaches the Lean kernel without an approval recorded here, so the
          kernel-check option stays off until every proposed axiom has a decision. Each card shows the
          plausibility estimate with its provenance (model, settings, prompt hash); it is an estimate, never a
          measured frequency.
          {!canReview && " This deployment is read-only: unlocked reviewer access is needed to run reports."}
        </p>
      </header>

      <section aria-labelledby="queue-input" className="mt-6 border border-[#c8cfdb] bg-background p-4">
        <h2 id="queue-input" className="section-label">Camp record and proposed candidates</h2>
        <div className="mt-2 grid gap-3 md:grid-cols-2">
          <div>
            <label htmlFor="queue-record" className="section-label block">Record JSON (from the Camps view's "Copy record JSON")</label>
            <textarea
              id="queue-record"
              value={recordText}
              rows={6}
              placeholder='{"camp": "…", "documents": […], "statements": […]}'
              onChange={(event) => setRecordText(event.target.value)}
              className="mt-1 w-full resize-y border border-[#aeb8c9] bg-[#f8f8f8] p-3 font-code text-xs placeholder:text-[#606a78]"
            />
          </div>
          <div>
            <label htmlFor="queue-candidates" className="section-label block">Candidates JSON (proposed unstated axioms with evidence quotes)</label>
            <textarea
              id="queue-candidates"
              value={candidatesText}
              rows={6}
              onChange={(event) => setCandidatesText(event.target.value)}
              className="mt-1 w-full resize-y border border-[#aeb8c9] bg-[#f8f8f8] p-3 font-code text-xs"
            />
          </div>
        </div>
        <div className="mt-3 flex flex-wrap items-end gap-3">
          <div>
            <label htmlFor="queue-lam" className="section-label block">λ (cost per axiom)</label>
            <input
              id="queue-lam"
              type="number"
              min={0.01}
              max={10}
              step={0.05}
              value={lam}
              onChange={(event) => setLam(Number(event.target.value))}
              className="mt-1 min-h-11 w-28 border border-[#aeb8c9] bg-[#f8f8f8] px-2 text-sm"
            />
          </div>
          <div>
            <label htmlFor="queue-maxchecks" className="section-label block">Check budget</label>
            <input
              id="queue-maxchecks"
              type="number"
              min={1}
              max={100000}
              step={50}
              value={maxChecks}
              onChange={(event) => setMaxChecks(Number(event.target.value))}
              className="mt-1 min-h-11 w-32 border border-[#aeb8c9] bg-[#f8f8f8] px-2 text-sm"
            />
          </div>
          <label className="flex min-h-11 items-center gap-2 border border-[#aeb8c9] px-3 text-sm">
            <input
              type="checkbox"
              checked={lean}
              disabled={!allReviewed}
              onChange={(event) => setLean(event.target.checked)}
            />
            Kernel-check with Lean {report && !allReviewed && "(needs a decision on every proposed axiom)"}
          </label>
          <button
            type="button"
            onClick={runReport}
            disabled={!canReview || run.isPending || !recordText.trim()}
            className="transition-ui inline-flex min-h-11 items-center gap-2 bg-primary px-4 font-semibold text-primary-foreground hover:bg-[#173f92] disabled:opacity-45"
          >
            <Play className="size-4" aria-hidden="true" />{run.isPending ? "Running…" : "Run camp report"}
          </button>
        </div>
        {inputError && <p role="alert" className="mt-3 bg-[#ffebe6] p-3 text-sm text-[#8a2d21]">{inputError}</p>}
      </section>

      {run.data?.kind === "no_verdict" && (
        <p role="status" className="mt-5 border border-[#d7ae4a] bg-[#fff0c2] p-4 text-sm text-[#694b00]">
          No verdict: {run.data.reason} A stopped or missing runtime is never a finding about the camp.
        </p>
      )}

      {report && (
        <div className="mt-6 space-y-5">
          <section aria-labelledby="queue-report-head" className="border border-[#c8cfdb] bg-background p-4">
            <div className="flex flex-wrap items-center gap-2">
              <h2 id="queue-report-head" className="font-semibold">Report for camp <code className="font-code">{report.camp}</code></h2>
              {report.search_complete ? (
                <StatusBadge tone="green" icon="check">SEARCH COMPLETE</StatusBadge>
              ) : (
                <StatusBadge tone="amber" icon="warning">SEARCH INCOMPLETE — certified, not shown cost-minimal</StatusBadge>
              )}
              <ExistenceBadge report={report} />
            </div>
            <p className="mt-2 text-sm text-[#4c5260]">
              Source: {provenanceLine(report.source)} · λ {report.lam} · {report.systems.length} selected system(s) ·{" "}
              {report.pool.candidates.length} proposed axiom(s), {report.pool.dropped.length} dropped
            </p>
            <div className="mt-3 space-y-2">
              {report.systems.map((_, index) => (
                <SystemCard key={index} report={report} index={index} />
              ))}
            </div>
          </section>

          <section aria-labelledby="queue-cards" className="space-y-3">
            <div className="flex flex-wrap items-center justify-between gap-3">
              <h2 id="queue-cards" className="flex items-center gap-2 font-semibold">
                <ListChecks className="size-5 text-primary" aria-hidden="true" /> Proposed axioms
              </h2>
              <button
                type="button"
                onClick={copyApproved}
                disabled={!canReview || !allReviewed}
                className="transition-ui inline-flex min-h-11 items-center gap-2 border border-primary px-4 text-sm font-semibold text-primary hover:bg-secondary disabled:opacity-50"
              >
                <ClipboardCheck className="size-4" aria-hidden="true" />
                {copied ? "Copied" : "Copy approved candidates JSON"}
              </button>
            </div>
            {report.pool.candidates.length === 0 && (
              <p className="border border-[#c5cbd4] bg-[#f1f2f4] p-3 text-sm text-[#3f4550]">No proposed axioms in this run.</p>
            )}
            {report.pool.candidates.map((candidate) => {
              const decision = queue.decisions[candidate.fol];
              return (
                <article key={candidate.fol} className="border border-[#c8cfdb] bg-background p-4">
                  <div className="flex flex-wrap items-center justify-between gap-2">
                    <span className="flex items-center gap-2 text-sm font-semibold">
                      <Bot className="size-4 text-primary" aria-hidden="true" /> Proposed axiom
                    </span>
                    {decision ? (
                      <StatusBadge tone={decision.status === "approved" ? "green" : "red"} icon={decision.status === "approved" ? "check" : "warning"}>
                        {decision.status === "approved" ? "Approved" : "Rejected"} · {decision.at.slice(0, 19).replace("T", " ")}
                      </StatusBadge>
                    ) : (
                      <StatusBadge tone="amber" icon="draft">Awaiting human decision</StatusBadge>
                    )}
                  </div>
                  <pre className="code-panel mt-3 whitespace-pre-wrap break-words p-3">{candidate.fol}</pre>
                  <p className="mt-2 text-sm">
                    Plausibility estimate: <strong>{candidate.plausibility}</strong>{" "}
                    {candidate.plausibility_source === "default"
                      ? `(anchored default ${report.plausibility.default} — nobody scored it)`
                      : "(scored with the review)"}
                    {" "}· provenance: {provenanceLine(report.source)}
                  </p>
                  <h3 className="section-label mt-3">Evidence quotes</h3>
                  <ul className="mt-1 space-y-1 text-sm">
                    {candidate.quotes.map((quote, i) => (
                      <li key={i} className="border-l-2 border-[#9aa5b6] pl-3">
                        <span className="font-code text-xs text-[#4c5260]">{quote[0]} · span [{quote[2][0]}, {quote[2][1]})</span>
                        <p className="italic">"{quote[1]}"</p>
                      </li>
                    ))}
                  </ul>
                  <label htmlFor={`note-${candidate.fol}`} className="section-label mt-3 block">Review note</label>
                  <textarea
                    id={`note-${candidate.fol}`}
                    rows={2}
                    value={notes[candidate.fol] ?? ""}
                    onChange={(event) => setNotes((current) => ({ ...current, [candidate.fol]: event.target.value }))}
                    placeholder="Why this axiom is or is not part of the camp's record…"
                    className="mt-1 w-full resize-y border border-[#aeb8c9] bg-[#f8f8f8] p-2 text-sm placeholder:text-[#606a78]"
                  />
                  <div className="mt-2 flex gap-2">
                    <button
                      type="button"
                      disabled={!canReview}
                      onClick={() => queue.decide(candidate.fol, "approved", notes[candidate.fol] ?? "")}
                      className="transition-ui inline-flex min-h-11 items-center gap-2 bg-primary px-4 text-sm font-semibold text-primary-foreground hover:bg-[#173f92] disabled:opacity-45"
                    >
                      <Check className="size-4" aria-hidden="true" /> Approve
                    </button>
                    <button
                      type="button"
                      disabled={!canReview}
                      onClick={() => queue.decide(candidate.fol, "rejected", notes[candidate.fol] ?? "")}
                      className="transition-ui inline-flex min-h-11 items-center gap-2 border border-[#a43b2c] px-4 text-sm font-semibold text-[#8a2d21] hover:bg-[#ffebe6] disabled:opacity-45"
                    >
                      <MessageSquareWarning className="size-4" aria-hidden="true" /> Reject
                    </button>
                  </div>
                  {decision?.note && <p className="mt-2 text-sm text-[#4c5260]">Note: {decision.note}</p>}
                </article>
              );
            })}
            {report.pool.dropped.length > 0 && (
              <div className="border border-[#c5cbd4] bg-[#f1f2f4] p-3 text-sm text-[#3f4550]">
                <h3 className="section-label">Dropped proposals</h3>
                <ul className="mt-1 space-y-1">
                  {report.pool.dropped.map((dropped) => (
                    <li key={dropped.fol}><code className="font-code text-xs">{dropped.fol}</code> — {dropped.reason}</li>
                  ))}
                </ul>
              </div>
            )}
          </section>
        </div>
      )}
    </div>
  );
}
