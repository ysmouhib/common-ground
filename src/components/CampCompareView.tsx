import { Plus, Scale, Trash2 } from "lucide-react";

import type { CrosscampReport } from "@contracts/crosscampReport";

import type { CampReport } from "@contracts/engineReport";

import { useCrosscamp } from "@/hooks/useCrosscamp";

import type { WorkspaceData } from "@/hooks/useWorkspace";

import { StatusBadge } from "./Status";

function CheckLine({ label, check }: { label: string; check: { outcome: string; badge: string; claim: string; detail: string } }) {
  const tone = check.outcome === "holds" ? "green" : check.outcome === "fails" ? "red" : "amber";
  return (
    <li className="flex flex-wrap items-center gap-2 text-sm">
      <StatusBadge tone={tone}>{check.outcome}</StatusBadge>
      <span className="font-semibold">{label}</span>
      <code className="font-code text-xs">{check.claim}</code>
      <span className="text-[#4c5260]">{check.badge}</span>
      <span className="w-full text-xs text-[#4c5260]">{check.detail}</span>
    </li>
  );
}

function AgreedList({ entries }: { entries: { statement: string; origin: string; id: string; checks: { outcome: string }[] }[] }) {
  if (entries.length === 0) return <p className="text-sm text-[#4c5260]">Nothing agreed.</p>;
  return (
    <ul className="space-y-1 text-sm">
      {entries.map((entry, i) => (
        <li key={i} className="flex flex-wrap items-center gap-2">
          <StatusBadge tone="green" icon="check">{entry.checks.length} camp(s) entail it</StatusBadge>
          <code className="font-code text-xs">{entry.statement}</code>
          <span className="text-[#4c5260]">{entry.origin} · {entry.id}</span>
        </li>
      ))}
    </ul>
  );
}

function StatedTier({ report }: { report: CrosscampReport }) {
  const stated = report.common_ground.stated;
  const faultStated = report.fault_lines.stated;
  return (
    <section aria-labelledby="cg-stated" className="border border-[#c8cfdb] bg-background p-4">
      <h3 id="cg-stated" className="font-semibold">Common ground among stated claims (invariant — holds for every reconstruction)</h3>
      <div className="mt-2 flex flex-wrap gap-2">
        <CheckLine label="Union of the camps' stated claims is consistent" check={stated.union_consistent} />
        {stated.vacuous_camps.length > 0 && (
          <StatusBadge tone="red" icon="warning">Vacuous for {stated.vacuous_camps.join(", ")} (inconsistent stated claims)</StatusBadge>
        )}
        {stated.pending_camps.length > 0 && (
          <StatusBadge tone="amber" icon="draft">Pending for {stated.pending_camps.join(", ")}</StatusBadge>
        )}
      </div>
      <ul className="mt-2 space-y-1 text-sm">
        {stated.camp_consistency.map((entry) => (
          <li key={entry.camp} className="flex flex-wrap items-center gap-2">
            <span className="font-semibold">{entry.camp}</span>
            <StatusBadge tone={entry.outcome === "holds" ? "green" : entry.outcome === "fails" ? "red" : "amber"}>{entry.outcome}</StatusBadge>
            <span className="text-[#4c5260]">{entry.badge}</span>
            <span className="w-full text-xs text-[#4c5260]">{entry.detail}</span>
          </li>
        ))}
      </ul>
      {stated.unformalized.length > 0 && (
        <p className="mt-2 border border-[#d7ae4a] bg-[#fff0c2] p-2 text-sm text-[#694b00]">
          {stated.unformalized.length} statement(s) have no reviewed formalization (
          {stated.unformalized.map((u) => `${u.camp}:${u.id}`).join(", ")}): no check covers them; consistency and
          the absence of conflict are PENDING for the whole record. They are listed, never dropped.
        </p>
      )}
      <h4 className="section-label mt-3">Agreed stated claims</h4>
      <AgreedList entries={stated.agreed} />
      <h4 className="section-label mt-3">Stated-tier fault lines</h4>
      {faultStated.mus === null || faultStated.mcs === null ? (
        <p className="text-sm text-[#694b00]">Pending — {faultStated.pending ?? "no verdict"}</p>
      ) : faultStated.mus.length === 0 ? (
        <p className="text-sm">
          No stated conflict{faultStated.complete ? " (established — the enumeration finished)" : " (over the formalized statements only)"}.
        </p>
      ) : (
        <div className="mt-1 grid gap-2 md:grid-cols-2">
          <div>
            <h5 className="section-label">Minimal conflicts (MUS)</h5>
            <ul className="space-y-1 text-sm">{faultStated.mus.map((mus, i) => (
              <li key={i}><code className="font-code text-xs">{mus.join("  ∧  ")}</code></li>
            ))}</ul>
          </div>
          <div>
            <h5 className="section-label">Smallest concessions (MCS)</h5>
            <ul className="space-y-1 text-sm">{faultStated.mcs.map((mcs, i) => (
              <li key={i}><code className="font-code text-xs">{mcs.join("  ∨  ")}</code></li>
            ))}</ul>
          </div>
        </div>
      )}
    </section>
  );
}

function SystemPairTier({ report }: { report: CrosscampReport }) {
  const pairs = report.common_ground.per_system_pair;
  const faultPairs = report.fault_lines.per_system_pair;
  if (pairs.length === 0) {
    return (
      <section className="border border-[#c8cfdb] bg-background p-4">
        <h3 className="font-semibold">Selection-relative sections</h3>
        <p className="mt-2 text-sm text-[#4c5260]">
          No certified system to compare — camps with no certified system:{" "}
          {report.fault_lines.no_certified_systems.join(", ") || "none"}.
        </p>
      </section>
    );
  }
  return (
    <div className="space-y-4">
      {pairs.map((pair, index) => {
        const fault = faultPairs[index];
        const pairKey = `${pair.camps.join("+")}@${index}`;
        // pairwise display: for more than two camps the root divergences are per camp pair
        const rootPairs = new Map<string, typeof fault.root_divergence>();
        for (const root of fault.root_divergence) {
          const key = `${root.camp1} × ${root.camp2}`;
          rootPairs.set(key, [...(rootPairs.get(key) ?? []), root]);
        }
        const pendingPairs = new Map<string, typeof fault.root_divergence_pending>();
        for (const root of fault.root_divergence_pending) {
          const key = `${root.camp1} × ${root.camp2}`;
          pendingPairs.set(key, [...(pendingPairs.get(key) ?? []), root]);
        }
        return (
          <section key={pairKey} aria-label={`System combination ${index + 1}`} className="border border-[#c8cfdb] bg-background p-4">
            <h3 className="font-semibold">Selected-system combination {index + 1}</h3>
            <ul className="mt-1 space-y-1 text-sm">
              {pair.camps.map((camp, i) => (
                <li key={camp}><span className="font-semibold">{camp}</span>: <code className="font-code text-xs">{(pair.systems[i] ?? []).join("  ∧  ") || "(empty system)"}</code></li>
              ))}
            </ul>
            <h4 className="section-label mt-3">Agreed among reconstructed axioms (selection-relative)</h4>
            <AgreedList entries={pair.agreed} />
            <h4 className="section-label mt-3">Fault lines of this combination</h4>
            {fault.mus === null ? (
              <p className="text-sm text-[#694b00]">Pending — {fault.pending ?? "no verdict"}</p>
            ) : fault.mus.length === 0 ? (
              <p className="text-sm">The systems are jointly consistent (union MUS empty).</p>
            ) : (
              <ul className="space-y-1 text-sm">{fault.mus.map((mus, i) => (
                <li key={i}><StatusBadge tone="red" icon="warning">conflict</StatusBadge> <code className="font-code text-xs">{mus.join("  ∧  ")}</code></li>
              ))}</ul>
            )}
            {report.camps.length > 2 && (
              <p className="mt-2 border border-[#c5cbd4] bg-[#f1f2f4] p-2 text-sm text-[#3f4550]">
                More than two camps: root divergences are shown pairwise per camp pair; a joint fault line over all
                camps at once is not computed (open question, cross-camp.md §9).
              </p>
            )}
            {[...rootPairs.entries()].map(([key, roots]) => (
              <div key={key} className="mt-2">
                <h5 className="section-label">Root divergence — {key} (rank = summed load, higher first)</h5>
                <ul className="space-y-1 text-sm">
                  {roots.map((root, i) => (
                    <li key={i} className="flex flex-wrap items-center gap-2">
                      <StatusBadge tone="red" icon="warning">rank {root.rank}{root.rank_is_lower_bound ? " (lower bound)" : ""}</StatusBadge>
                      <code className="font-code text-xs">{root.a1}</code> <span className="text-[#4c5260]">vs</span> <code className="font-code text-xs">{root.a2}</code>
                    </li>
                  ))}
                </ul>
              </div>
            ))}
            {pendingPairs.size > 0 && (
              <div className="mt-2 border border-[#d7ae4a] bg-[#fff0c2] p-2">
                <h5 className="section-label text-[#694b00]">Pending root-divergence pairs (no verdict — never dropped)</h5>
                <ul className="space-y-1 text-sm text-[#694b00]">
                  {[...pendingPairs.entries()].flatMap(([key, roots]) =>
                    roots.map((root, i) => (
                      <li key={`${key}-${i}`}>{key}: <code className="font-code text-xs">{root.a1}</code> vs <code className="font-code text-xs">{root.a2}</code> — {root.pending}</li>
                    )),
                  )}
                </ul>
              </div>
            )}
          </section>
        );
      })}
    </div>
  );
}

function CampSummaries({ camps }: { camps: Record<string, CampReport> }) {
  return (
    <section aria-labelledby="compare-camps" className="border border-[#c8cfdb] bg-background p-4">
      <h3 id="compare-camps" className="font-semibold">Per-camp reports</h3>
      <ul className="mt-2 space-y-1 text-sm">
        {Object.entries(camps).map(([camp, report]) => (
          <li key={camp} className="flex flex-wrap items-center gap-2">
            <span className="font-semibold">{camp}</span>
            {report.search_complete ? (
              <StatusBadge tone="green" icon="check">SEARCH COMPLETE</StatusBadge>
            ) : (
              <StatusBadge tone="amber" icon="warning">SEARCH INCOMPLETE</StatusBadge>
            )}
            <StatusBadge tone={report.existence.status === "certified" ? "green" : report.existence.status === "none" ? "red" : "amber"}>
              existence: {report.existence.status}
            </StatusBadge>
            {report.systems.map((system, i) => (
              <StatusBadge key={i} tone={system.certified ? "green" : "neutral"}>{system.badge}</StatusBadge>
            ))}
          </li>
        ))}
      </ul>
    </section>
  );
}

export function CampCompareView({ workspace }: { workspace: WorkspaceData }) {
  const { pairs, lam, setLam, maxChecks, setMaxChecks, lean, setLean, addPair, removePair, updatePair, run, runAll, parseError } = useCrosscamp();
  const canReview = workspace.access.isReviewer;
  const result = run.data?.kind === "report" ? run.data : undefined;

  return (
    <div className="py-8">
      <header className="max-w-3xl">
        <h1 className="text-3xl font-semibold tracking-[-0.02em]">Compare camps</h1>
        <p className="mt-3 text-sm leading-relaxed text-[#4c5260]">
          Two or more camp records (copy each from the Camps view) with their candidates, in the same order. The report
          shows the two common-ground tiers and the fault-line section exactly as certified: search-incomplete camps
          are marked, pending root-divergence pairs are listed, and unformalized statements stay visible.
          {!canReview && " This deployment is read-only: unlocked reviewer access is needed to run the comparison."}
        </p>
      </header>

      <section aria-labelledby="compare-input" className="mt-6 space-y-3">
        <h2 id="compare-input" className="section-label">Camp records and candidates (one pair per camp)</h2>
        {pairs.map((pair, index) => (
          <div key={pair.id} className="grid gap-3 border border-[#c8cfdb] bg-background p-4 md:grid-cols-2">
            <div>
              <label htmlFor={`rec-${pair.id}`} className="section-label block">Record JSON — camp {index + 1}</label>
              <textarea
                id={`rec-${pair.id}`}
                value={pair.recordText}
                rows={5}
                placeholder='{"camp": "…", "documents": […], "statements": […]}'
                onChange={(event) => updatePair(pair.id, { recordText: event.target.value })}
                className="mt-1 w-full resize-y border border-[#aeb8c9] bg-[#f8f8f8] p-3 font-code text-xs placeholder:text-[#606a78]"
              />
            </div>
            <div>
              <label htmlFor={`cand-${pair.id}`} className="section-label block">Candidates JSON — camp {index + 1}</label>
              <textarea
                id={`cand-${pair.id}`}
                value={pair.candidatesText}
                rows={5}
                onChange={(event) => updatePair(pair.id, { candidatesText: event.target.value })}
                className="mt-1 w-full resize-y border border-[#aeb8c9] bg-[#f8f8f8] p-3 font-code text-xs"
              />
            </div>
            <div className="flex items-center gap-2 md:col-span-2">
              {pairs.length > 2 && (
                <button
                  type="button"
                  onClick={() => removePair(pair.id)}
                  className="transition-ui inline-flex min-h-11 items-center gap-2 border border-[#a43b2c] px-3 text-sm font-semibold text-[#8a2d21] hover:bg-[#ffebe6]"
                >
                  <Trash2 className="size-4" aria-hidden="true" />Remove this camp
                </button>
              )}
            </div>
          </div>
        ))}
        <div className="flex flex-wrap items-end gap-3">
          <button
            type="button"
            onClick={addPair}
            disabled={pairs.length >= 8}
            className="transition-ui inline-flex min-h-11 items-center gap-2 border border-[#8b93a2] px-4 text-sm font-semibold hover:bg-secondary disabled:opacity-45"
          >
            <Plus className="size-4" aria-hidden="true" />Add a camp
          </button>
          <div>
            <label htmlFor="xc-lam" className="section-label block">λ</label>
            <input id="xc-lam" type="number" min={0.01} max={10} step={0.05} value={lam}
              onChange={(event) => setLam(Number(event.target.value))}
              className="mt-1 min-h-11 w-24 border border-[#aeb8c9] bg-[#f8f8f8] px-2 text-sm" />
          </div>
          <div>
            <label htmlFor="xc-maxchecks" className="section-label block">Check budget per camp</label>
            <input id="xc-maxchecks" type="number" min={1} max={100000} step={50} value={maxChecks}
              onChange={(event) => setMaxChecks(Number(event.target.value))}
              className="mt-1 min-h-11 w-32 border border-[#aeb8c9] bg-[#f8f8f8] px-2 text-sm" />
          </div>
          <label className="flex min-h-11 items-center gap-2 border border-[#aeb8c9] px-3 text-sm">
            <input type="checkbox" checked={lean} onChange={(event) => setLean(event.target.checked)} />
            Kernel-check with Lean
          </label>
          <button
            type="button"
            onClick={runAll}
            disabled={!canReview || run.isPending || pairs.length < 2}
            className="transition-ui inline-flex min-h-11 items-center gap-2 bg-primary px-4 font-semibold text-primary-foreground hover:bg-[#173f92] disabled:opacity-45"
          >
            <Scale className="size-4" aria-hidden="true" />{run.isPending ? "Running…" : "Run cross-camp report"}
          </button>
        </div>
        {parseError && <p role="alert" className="bg-[#ffebe6] p-3 text-sm text-[#8a2d21]">{parseError}</p>}
      </section>

      {run.data?.kind === "no_verdict" && (
        <p role="status" className="mt-5 border border-[#d7ae4a] bg-[#fff0c2] p-4 text-sm text-[#694b00]">
          No verdict: {run.data.reason} A stopped or missing runtime is never a finding about the camps.
        </p>
      )}

      {result && (
        <div className="mt-6 space-y-4">
          <div className="border border-[#c8cfdb] bg-background p-4">
            <div className="flex flex-wrap items-center gap-2">
              <h2 className="font-semibold">Cross-camp report — {result.report.camps.join(" vs ")}</h2>
            </div>
            {result.report.search_incomplete.length > 0 && (
              <p role="alert" className="mt-2 border border-[#d7ae4a] bg-[#fff0c2] p-3 text-sm text-[#694b00]">
                Search incomplete for {result.report.search_incomplete.map((c) => `\`${c}\``).join(", ")}: the check
                budget stopped that search. The systems compared are certified, but not shown to be cost-minimal, so the
                selection-relative sections are provisional. The stated-claim sections do not depend on the search.
              </p>
            )}
          </div>
          <CampSummaries camps={result.camps} />
          <StatedTier report={result.report} />
          <SystemPairTier report={result.report} />
        </div>
      )}
    </div>
  );
}
