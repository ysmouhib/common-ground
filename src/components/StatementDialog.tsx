import { useState } from "react";
import { ArrowUpRight, Bot, Check, FileClock, MessageSquareWarning, PencilLine } from "lucide-react";
import type { Statement, WorkspaceData } from "@/hooks/useWorkspace";
import { trpc } from "@/providers/trpc";
import { ApprovalBadge, ProofBadge, StatusBadge } from "./Status";
import {
  Dialog,
  DialogContent,
  DialogDescription,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

interface Props {
  statement: Statement | undefined;
  workspace: WorkspaceData;
  open: boolean;
  onOpenChange: (open: boolean) => void;
  onOpenProof: (proofId: string) => void;
}

export function StatementDialog({ statement, workspace, open, onOpenChange, onOpenProof }: Props) {
  const [note, setNote] = useState("");
  const [message, setMessage] = useState("");
  const [aiError, setAiError] = useState("");
  const utils = trpc.useUtils();

  const review = trpc.workspace.setStatementStatus.useMutation({
    onSuccess: async (_, variables) => {
      setMessage(`Review saved: ${variables.status}. Dependent certificate states were recalculated.`);
      setNote("");
      await utils.workspace.get.invalidate();
    },
    onError: (error) => setMessage(error.message),
  });
  const critique = trpc.ai.critiqueFormalization.useMutation({
    onSuccess: async () => {
      setAiError("");
      await utils.workspace.get.invalidate();
    },
    onError: (error) => setAiError(error.message),
  });

  if (!statement) return null;
  const linkedEvidence = workspace.evidence.find((item) => item.id === statement.evidenceId);
  const dependentProofs = workspace.proofs.filter((proof) => proof.premiseIds.includes(statement.id));
  const drafts = workspace.aiDrafts.filter((draft) => draft.statementId === statement.id);
  const events = workspace.reviewEvents.filter((event) => event.statementId === statement.id);

  function saveReview(status: "approved" | "disputed" | "draft") {
    if (!statement) return;
    setMessage("");
    review.mutate({ statementId: statement.id, status, note });
  }

  return (
    <Dialog open={open} onOpenChange={onOpenChange}>
      <DialogContent className="max-h-[92dvh] overflow-y-auto rounded-none p-0 sm:max-w-3xl">
        <div className="border-b-4 border-primary px-6 py-6 sm:px-8">
          <DialogHeader>
            <div className="flex flex-wrap items-center gap-2 pr-8">
              <span className="font-code text-xs font-semibold text-primary">{statement.id}</span>
              <StatusBadge tone="blue">{statement.kind}</StatusBadge>
              <ApprovalBadge status={statement.approvalStatus} />
              {statement.isWorkshop && <StatusBadge tone="amber">Facilitator-created</StatusBadge>}
            </div>
            <DialogTitle className="pt-2 text-2xl leading-tight">{statement.title}</DialogTitle>
            <DialogDescription className="max-w-2xl text-base leading-relaxed text-[#444]">
              {statement.body}
            </DialogDescription>
          </DialogHeader>
        </div>

        <div className="grid gap-7 px-6 py-6 sm:px-8">
          <section aria-labelledby="formal-reading">
            <h3 id="formal-reading" className="section-label mb-2">Formal reading</h3>
            <pre className="code-panel whitespace-pre-wrap break-words p-4">{statement.formalText}</pre>
            <p className="mt-3 text-sm leading-relaxed text-[#4c5260]">{statement.formalizationNote}</p>
          </section>

          {linkedEvidence && (
            <section aria-labelledby="linked-source" className="border border-[#c8cfdb] p-4">
              <div className="flex items-start justify-between gap-4">
                <div>
                  <h3 id="linked-source" className="font-semibold leading-snug">{linkedEvidence.title}</h3>
                  <p className="mt-1 text-sm text-[#4c5260]">{linkedEvidence.publisher} · {linkedEvidence.publishedAt}</p>
                </div>
                <a
                  href={linkedEvidence.url}
                  target="_blank"
                  rel="noreferrer"
                  className="inline-flex min-h-11 shrink-0 items-center gap-1 text-sm font-semibold text-primary underline underline-offset-4"
                >
                  Source <ArrowUpRight className="size-4" aria-hidden="true" />
                </a>
              </div>
              <p className="mt-3 text-sm"><strong>Limit:</strong> {linkedEvidence.limitation}</p>
            </section>
          )}

          {dependentProofs.length > 0 && (
            <section aria-labelledby="dependent-proofs">
              <h3 id="dependent-proofs" className="section-label mb-3">Dependent certificates</h3>
              <div className="divide-y border-y">
                {dependentProofs.map((proof) => (
                  <button
                    key={proof.id}
                    type="button"
                    onClick={() => onOpenProof(proof.id)}
                    className="transition-ui flex min-h-14 w-full items-center justify-between gap-3 py-3 text-left hover:bg-secondary"
                  >
                    <span className="font-medium">{proof.title}</span>
                    <ProofBadge proof={proof} />
                  </button>
                ))}
              </div>
            </section>
          )}

          <section aria-labelledby="human-review" className="bg-[#f0f2f5] p-5">
            <div className="flex items-center gap-2">
              <PencilLine className="size-5 text-primary" aria-hidden="true" />
              <h3 id="human-review" className="font-semibold">Human review decision</h3>
            </div>
            <p className="mt-2 text-sm text-[#4c5260]">
              Review the meaning, not just the logic. Changing a premise’s status immediately activates or suspends dependent certificates.
            </p>
            <label htmlFor={`review-note-${statement.id}`} className="section-label mt-4 block">Review note</label>
            <textarea
              id={`review-note-${statement.id}`}
              value={note}
              onChange={(event) => setNote(event.target.value)}
              rows={3}
              placeholder="Explain what was checked or contested…"
              className="mt-2 w-full resize-y border border-[#aeb8c9] bg-[#f8f8f8] p-3 text-base text-foreground placeholder:text-[#606a78]"
            />
            {note.trim().length > 0 && note.trim().length < 3 && (
              <p className="mt-1 text-sm text-[#8a2d21]">Add at least three characters.</p>
            )}
            <div className="mt-3 flex flex-col gap-2 sm:flex-row">
              <button
                type="button"
                disabled={note.trim().length < 3 || review.isPending}
                onClick={() => saveReview("approved")}
                className="transition-ui inline-flex min-h-11 items-center justify-center gap-2 bg-primary px-4 font-semibold text-primary-foreground hover:bg-[#173f92] disabled:opacity-45"
              >
                <Check className="size-4" aria-hidden="true" /> Approve
              </button>
              <button
                type="button"
                disabled={note.trim().length < 3 || review.isPending}
                onClick={() => saveReview("disputed")}
                className="transition-ui inline-flex min-h-11 items-center justify-center gap-2 border border-[#a43b2c] px-4 font-semibold text-[#8a2d21] hover:bg-[#ffebe6] disabled:opacity-45"
              >
                <MessageSquareWarning className="size-4" aria-hidden="true" /> Dispute
              </button>
              <button
                type="button"
                disabled={note.trim().length < 3 || review.isPending}
                onClick={() => saveReview("draft")}
                className="transition-ui min-h-11 border border-[#8b93a2] px-4 font-semibold hover:bg-muted disabled:opacity-45"
              >
                Mark draft
              </button>
            </div>
            {message && <p role="status" className="mt-3 border border-[#b7bfcd] bg-background p-3 text-sm">{message}</p>}
          </section>

          <section aria-labelledby="ai-review" className="border-t pt-6">
            <div className="flex flex-col justify-between gap-3 sm:flex-row sm:items-center">
              <div>
                <div className="flex items-center gap-2">
                  <Bot className="size-5 text-primary" aria-hidden="true" />
                  <h3 id="ai-review" className="font-semibold">AI interpretation check</h3>
                </div>
                <p className="mt-1 max-w-xl text-sm text-[#4c5260]">
                  Generate an alternative formal reading and back-translation. The result is a review draft; it changes neither the canonical statement nor any Lean proof.
                </p>
              </div>
              <button
                type="button"
                onClick={() => critique.mutate({ statementId: statement.id })}
                disabled={critique.isPending}
                className="transition-ui min-h-11 shrink-0 border border-primary px-4 font-semibold text-primary hover:bg-secondary disabled:opacity-50"
              >
                {critique.isPending ? "Generating draft…" : "Test this encoding"}
              </button>
            </div>
            {aiError && <p role="alert" className="mt-3 bg-[#ffebe6] p-3 text-sm text-[#8a2d21]">{aiError}</p>}
            {drafts.length > 0 && (
              <div className="mt-4 space-y-2">
                {drafts.map((draft) => (
                  <details key={draft.id} className="border border-[#c8cfdb] bg-background p-4">
                    <summary className="min-h-7 cursor-pointer font-semibold">AI review draft · {draft.createdAt.toLocaleString()}</summary>
                    <div className="mt-4 grid gap-4">
                      <div>
                        <h4 className="section-label mb-2">Proposed expression</h4>
                        <pre className="code-panel whitespace-pre-wrap p-3">{draft.proposedFormal}</pre>
                      </div>
                      <div>
                        <h4 className="section-label mb-1">Back-translation</h4>
                        <p className="text-sm">{draft.backTranslation}</p>
                      </div>
                      <div>
                        <h4 className="section-label mb-1">Interpretation notes</h4>
                        <p className="whitespace-pre-line text-sm">{draft.interpretationNotes}</p>
                      </div>
                    </div>
                  </details>
                ))}
              </div>
            )}
          </section>

          {events.length > 0 && (
            <section aria-labelledby="statement-history">
              <h3 id="statement-history" className="section-label mb-3 flex items-center gap-2">
                <FileClock className="size-4" aria-hidden="true" /> Review history
              </h3>
              <ol className="space-y-3">
                {events.map((event) => (
                  <li key={event.id} className="border-l border-[#9aa5b6] pl-4 text-sm">
                    <strong>{event.action.replaceAll("_", " ")}</strong> · {event.createdAt.toLocaleString()}
                    <p className="mt-1 text-[#4c5260]">{event.note}</p>
                  </li>
                ))}
              </ol>
            </section>
          )}
        </div>
      </DialogContent>
    </Dialog>
  );
}
