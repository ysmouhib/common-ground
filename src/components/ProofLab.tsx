import { useMemo, useState } from "react";
import { Check, Clipboard, FlaskConical, Play, RotateCcw, ShieldCheck } from "lucide-react";
import { buildLeanSource, buildNegativeControlSource, LEAN_TOOLCHAIN } from "@contracts/lean";
import type { WorkspaceData } from "@/hooks/useWorkspace";
import { trpc } from "@/providers/trpc";
import { ApprovalBadge, ProofBadge, StatusBadge } from "./Status";

interface Props {
  workspace: WorkspaceData;
  selectedProofId: string;
  onSelectProof: (id: string) => void;
  onOpenStatement: (id: string) => void;
}

export function ProofLab({ workspace, selectedProofId, onSelectProof, onOpenStatement }: Props) {
  const [copied, setCopied] = useState(false);
  const [runMessage, setRunMessage] = useState("");
  const utils = trpc.useUtils();
  const proof = workspace.proofs.find((item) => item.id === selectedProofId) ?? workspace.proofs[0];
  const canReview = workspace.access.isReviewer;

  const verify = trpc.proof.verify.useMutation({
    onSuccess: async (result) => {
      setRunMessage(
        !result.runtimeAvailable || result.timedOut
          ? result.output
          : result.expectedOutcome
            ? result.accepted
              ? "Lean accepted the proof and the axiom audit completed."
              : "Lean rejected the invalid inference, as expected."
            : "Unexpected verifier outcome. Inspect the diagnostics before trusting this result.",
      );
      await utils.workspace.get.invalidate();
    },
    onError: (error) => setRunMessage(error.message),
  });
  const verifyAll = trpc.proof.verifyAll.useMutation({
    onSuccess: async (results) => {
      const available = results.some((result) => result.runtimeAvailable);
      const unfinished = results.filter((result) => result.timedOut).length;
      const allExpected = available && results.length === 5 && results.every((result) => result.expectedOutcome);
      setRunMessage(
        allExpected
          ? "Verification batch finished: four valid certificates were accepted and the invalid inference was rejected."
          : unfinished > 0
            ? `Lean did not finish ${unfinished} of ${results.length} runs in time, so those have no verdict and their stored certificates are unchanged. The first batch after a restart is the slowest: run it again.`
            : available
              ? "Unexpected verifier outcome in the batch. Inspect each certificate’s diagnostics before trusting the result."
              : "No live Lean runtime is available. Stored build-time certificates were left unchanged.",
      );
      await utils.workspace.get.invalidate();
    },
    onError: (error) => setRunMessage(error.message),
  });

  const fullSource = useMemo(
    () => (proof?.isNegativeControl ? buildNegativeControlSource() : proof ? buildLeanSource(proof.theoremName) : ""),
    [proof],
  );

  if (!proof) return null;
  const runs = workspace.verificationRuns.filter((run) => run.proofId === proof.id);

  async function copySource() {
    await navigator.clipboard.writeText(fullSource);
    setCopied(true);
  }

  return (
    <div className="py-8 lg:py-10">
      <div className="flex flex-col justify-between gap-5 border-b border-[#bfc6d2] pb-7 lg:flex-row lg:items-end">
        <div>
          <div className="section-label flex items-center gap-2 text-primary"><ShieldCheck className="size-4" aria-hidden="true" /> Lean-backed proof laboratory</div>
          <h1 className="mt-2 text-4xl font-semibold tracking-[-0.035em]">Inspect the certificate, not a confidence score.</h1>
          <p className="mt-3 max-w-3xl text-[#4c5260]">
            Every active certificate combines three checks: current source hash, kernel acceptance, and approved premises. The negative control must fail.
          </p>
        </div>
        <button
          type="button"
          onClick={() => verifyAll.mutate()}
          disabled={!canReview || verifyAll.isPending || verify.isPending}
          title={canReview ? undefined : "Re-running Lean needs reviewer access."}
          className="transition-ui inline-flex min-h-11 shrink-0 items-center justify-center gap-2 border border-primary px-4 font-semibold text-primary hover:bg-secondary disabled:opacity-50"
        >
          <RotateCcw className={`size-4 ${verifyAll.isPending ? "animate-spin" : ""}`} aria-hidden="true" />
          {verifyAll.isPending ? "Running five checks…" : "Verify all + negative control"}
        </button>
      </div>

      <div className="grid lg:grid-cols-[300px_minmax(0,1fr)]">
        <aside className="border-b border-[#bfc6d2] py-5 lg:border-b-0 lg:border-r lg:pr-5">
          <div className="section-label mb-3">Certificates</div>
          <div className="grid gap-2 sm:grid-cols-2 lg:grid-cols-1">
            {workspace.proofs.map((item) => (
              <button
                type="button"
                key={item.id}
                onClick={() => onSelectProof(item.id)}
                aria-pressed={item.id === proof.id}
                className={`transition-ui min-h-20 border p-3 text-left ${item.id === proof.id ? "border-primary bg-[#eaf0ff]" : "border-[#c8cfdb] hover:bg-secondary"}`}
              >
                <span className="block font-code text-xs font-semibold text-primary">{item.theoremName}</span>
                <span className="mt-1 block text-sm font-medium leading-snug">{item.title}</span>
              </button>
            ))}
          </div>
          <div className="mt-5 text-xs leading-relaxed text-[#4c5260]">
            Pinned toolchain: {LEAN_TOOLCHAIN}. No mathlib dependency. Verification is limited to the explicit formal model.
          </div>
        </aside>

        <section className="min-w-0 py-6 lg:pl-8 lg:pt-0" aria-live="polite">
          <div className="flex flex-col justify-between gap-4 sm:flex-row sm:items-start">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <ProofBadge proof={proof} />
                {proof.isNegativeControl && <StatusBadge tone="amber" icon="test">Expected failure</StatusBadge>}
              </div>
              <h2 className="mt-3 text-2xl font-semibold leading-tight sm:text-3xl">{proof.title}</h2>
              <p className="mt-2 max-w-3xl text-[#4c5260]">{proof.description}</p>
            </div>
            <button
              type="button"
              onClick={() => verify.mutate({ proofId: proof.id })}
              disabled={!canReview || verify.isPending || verifyAll.isPending}
              title={canReview ? undefined : "Re-running Lean needs reviewer access."}
              className="transition-ui inline-flex min-h-11 shrink-0 items-center justify-center gap-2 bg-primary px-4 font-semibold text-primary-foreground hover:bg-[#173f92] disabled:opacity-50"
            >
              <Play className="size-4" aria-hidden="true" />
              {verify.isPending ? "Lean is checking…" : proof.isNegativeControl ? "Run negative control" : "Re-run Lean"}
            </button>
          </div>

          {runMessage && (
            <p role="status" className={`mt-5 border p-4 text-sm ${runMessage.includes("Unexpected") || runMessage.includes("unavailable") || runMessage.includes("did not finish") ? "border-[#d7ae4a] bg-[#fff0c2] text-[#694b00]" : "border-[#9cadd7] bg-[#eaf0ff] text-[#173f92]"}`}>
              {runMessage}
            </p>
          )}

          {!proof.isNegativeControl && proof.missingPremiseIds.length > 0 && (
            <div className="mt-5 border border-[#d7ae4a] bg-[#fff0c2] p-4 text-[#694b00]">
              <strong>Certificate inactive.</strong> Review or restore these premises: {proof.missingPremiseIds.join(", ")}. The kernel result remains separate from participant approval.
            </div>
          )}

          <section aria-labelledby="dependencies" className="mt-7">
            <h3 id="dependencies" className="section-label mb-3">Declared dependencies</h3>
            <div>
              {proof.premiseIds.map((id) => {
                const statement = workspace.statements.find((item) => item.id === id);
                if (!statement) return null;
                return (
                  <div key={id} className="proof-line flex gap-3 py-2">
                    <span className="proof-node">{id}</span>
                    <button
                      type="button"
                      onClick={() => onOpenStatement(id)}
                      className="transition-ui flex min-h-14 flex-1 flex-col justify-between gap-2 border-b border-[#d5d9df] px-1 py-2 text-left hover:bg-secondary sm:flex-row sm:items-center"
                    >
                      <span>
                        <span className="block font-medium leading-snug">{statement.title}</span>
                        <span className="mt-0.5 block text-sm text-[#4c5260]">{statement.kind}</span>
                      </span>
                      <ApprovalBadge status={statement.approvalStatus} />
                    </button>
                  </div>
                );
              })}
            </div>
          </section>

          <section aria-labelledby="lean-source" className="mt-7">
            <div className="flex items-center justify-between gap-3">
              <h3 id="lean-source" className="section-label">Lean theorem</h3>
              <button
                type="button"
                onClick={copySource}
                className="transition-ui inline-flex min-h-11 items-center gap-2 px-3 text-sm font-semibold text-primary hover:bg-secondary"
              >
                {copied ? <Check className="size-4" aria-hidden="true" /> : <Clipboard className="size-4" aria-hidden="true" />}
                {copied ? "Copied full file" : "Copy full checked file"}
              </button>
            </div>
            <pre className="code-panel mt-2 max-h-[430px] overflow-auto p-4">{proof.leanCode}</pre>
          </section>

          <section aria-labelledby="axiom-audit" className="mt-7 grid gap-5 md:grid-cols-2">
            <div>
              <h3 id="axiom-audit" className="section-label mb-2">Kernel & axiom audit</h3>
              <pre className="code-panel min-h-28 whitespace-pre-wrap break-words p-4">{proof.verifierOutput ?? "No verification output has been imported yet."}</pre>
            </div>
            <div className="text-sm">
              <h3 className="section-label mb-2">Certificate identity</h3>
              <dl className="space-y-2">
                <div><dt className="inline font-semibold">Toolchain: </dt><dd className="inline">{proof.toolchain ?? LEAN_TOOLCHAIN}</dd></div>
                <div><dt className="block font-semibold">SHA-256 source hash</dt><dd className="mt-1 break-all font-code text-xs text-[#4c5260]">{proof.proofHash ?? "Not recorded"}</dd></div>
                <div><dt className="inline font-semibold">Checked: </dt><dd className="inline">{proof.verifiedAt?.toLocaleString() ?? "Not recorded"}</dd></div>
              </dl>
            </div>
          </section>

          {runs.length > 0 && (
            <section aria-labelledby="run-history" className="mt-7 border-t pt-5">
              <h3 id="run-history" className="section-label mb-3 flex items-center gap-2"><FlaskConical className="size-4" aria-hidden="true" /> Verification history</h3>
              <div className="space-y-2">
                {runs.map((run) => (
                  <details key={run.id} className="border border-[#c8cfdb] p-3">
                    <summary className="cursor-pointer text-sm font-semibold">{run.outcome} · {run.createdAt.toLocaleString()}</summary>
                    <pre className="code-panel mt-3 max-h-64 overflow-auto whitespace-pre-wrap p-3">{run.output}</pre>
                  </details>
                ))}
              </div>
            </section>
          )}
        </section>
      </div>
    </div>
  );
}
