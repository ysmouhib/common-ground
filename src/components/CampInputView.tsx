import { useMemo, useState } from "react";

import { Copy, FileText, Plus, Trash2, Users } from "lucide-react";

import { buildRecord, STANCES, useCampDraft, type DraftCamp, type DraftStance } from "@/hooks/useCampDraft";

import type { WorkspaceData } from "@/hooks/useWorkspace";

import { StatusBadge } from "./Status";

function CampCard({
  camp,
  onUpdate,
  onRemove,
  onAddDocument,
  onUpdateDocument,
  onRemoveDocument,
  onAddStatement,
  onUpdateStatement,
  onRemoveStatement,
}: {
  camp: DraftCamp;
  onUpdate: (patch: Partial<Omit<DraftCamp, "id">>) => void;
  onRemove: () => void;
  onAddDocument: () => void;
  onUpdateDocument: (docId: string, text: string) => void;
  onRemoveDocument: (docId: string) => void;
  onAddStatement: (documentId: string) => void;
  onUpdateStatement: (statementId: string, patch: Partial<{ documentId: string; quote: string; stance: DraftStance; fol: string | null }>) => void;
  onRemoveStatement: (statementId: string) => void;
}) {
  const [copied, setCopied] = useState(false);
  const built = useMemo(() => buildRecord(camp), [camp]);

  function copyRecord() {
    if (!built.record) return;
    void navigator.clipboard.writeText(JSON.stringify(built.record, null, 2));
    setCopied(true);
    window.setTimeout(() => setCopied(false), 2000);
  }

  return (
    <section aria-label={`Camp ${camp.name || camp.id}`} className="border border-[#c8cfdb] bg-background">
      <div className="flex flex-wrap items-center justify-between gap-3 border-b border-[#d5d9df] bg-[#f0f2f5] px-4 py-3">
        <div className="flex min-w-0 items-center gap-2">
          <Users className="size-4 shrink-0 text-primary" aria-hidden="true" />
          <label htmlFor={`camp-name-${camp.id}`} className="section-label">Camp name</label>
          <input
            id={`camp-name-${camp.id}`}
            value={camp.name}
            maxLength={64}
            onChange={(event) => onUpdate({ name: event.target.value })}
            className="min-h-11 w-48 border border-[#aeb8c9] bg-[#f8f8f8] px-3 text-sm"
          />
        </div>
        <div className="flex items-center gap-2">
          <button
            type="button"
            onClick={copyRecord}
            disabled={!built.record}
            className="transition-ui inline-flex min-h-11 items-center gap-2 border border-[#8b93a2] px-3 text-sm font-semibold hover:bg-secondary disabled:opacity-45"
          >
            <Copy className="size-4" aria-hidden="true" />{copied ? "Copied" : "Copy record JSON"}
          </button>
          <button
            type="button"
            onClick={onRemove}
            aria-label={`Remove camp ${camp.name || camp.id}`}
            className="transition-ui inline-flex min-h-11 items-center gap-2 border border-[#a43b2c] px-3 text-sm font-semibold text-[#8a2d21] hover:bg-[#ffebe6]"
          >
            <Trash2 className="size-4" aria-hidden="true" />Remove
          </button>
        </div>
      </div>

      <div className="grid gap-5 px-4 py-4">
        {camp.documents.map((doc) => (
          <div key={doc.id} className="border border-[#d5d9df] p-3">
            <div className="flex items-center justify-between gap-2">
              <span className="section-label flex items-center gap-1.5">
                <FileText className="size-3.5" aria-hidden="true" />Document {doc.id}
              </span>
              <div className="flex gap-2">
                <button
                  type="button"
                  onClick={() => onAddStatement(doc.id)}
                  className="transition-ui inline-flex min-h-9 items-center gap-1 border border-primary px-2 text-xs font-semibold text-primary hover:bg-secondary"
                >
                  <Plus className="size-3.5" aria-hidden="true" />Add statement
                </button>
                <button
                  type="button"
                  onClick={() => onRemoveDocument(doc.id)}
                  aria-label={`Remove document ${doc.id}`}
                  className="transition-ui inline-flex min-h-9 items-center border border-[#a43b2c] px-2 text-xs font-semibold text-[#8a2d21] hover:bg-[#ffebe6]"
                >
                  <Trash2 className="size-3.5" aria-hidden="true" />
                </button>
              </div>
            </div>
            <textarea
              aria-label={`Text of document ${doc.id}`}
              value={doc.text}
              rows={4}
              placeholder="Paste the camp's text here; statements quote it verbatim…"
              onChange={(event) => onUpdateDocument(doc.id, event.target.value)}
              className="mt-2 w-full resize-y border border-[#aeb8c9] bg-[#f8f8f8] p-3 text-sm placeholder:text-[#606a78]"
            />
            <ul className="mt-2 space-y-2">
              {camp.statements
                .filter((st) => st.documentId === doc.id)
                .map((st) => (
                  <li key={st.id} className="border border-[#e2e6ec] bg-[#f8f8f8] p-3">
                    <div className="flex flex-wrap items-center justify-between gap-2">
                      <span className="font-code text-xs font-semibold text-primary">{st.id}</span>
                      {st.fol && st.fol.trim() ? (
                        <StatusBadge tone="blue">Formalized</StatusBadge>
                      ) : (
                        <StatusBadge tone="amber" icon="draft">PENDING — no reviewed formalization</StatusBadge>
                      )}
                      <button
                        type="button"
                        onClick={() => onRemoveStatement(st.id)}
                        aria-label={`Remove statement ${st.id}`}
                        className="transition-ui inline-flex min-h-9 items-center border border-[#a43b2c] px-2 text-xs font-semibold text-[#8a2d21] hover:bg-[#ffebe6]"
                      >
                        <Trash2 className="size-3.5" aria-hidden="true" />
                      </button>
                    </div>
                    <label className="section-label mt-2 block" htmlFor={`quote-${st.id}`}>Quote (verbatim from the document)</label>
                    <textarea
                      id={`quote-${st.id}`}
                      value={st.quote}
                      rows={2}
                      onChange={(event) => onUpdateStatement(st.id, { quote: event.target.value })}
                      className="mt-1 w-full resize-y border border-[#aeb8c9] bg-background p-2 text-sm"
                    />
                    <div className="mt-2 flex flex-col gap-2 sm:flex-row">
                      <div>
                        <label className="section-label block" htmlFor={`stance-${st.id}`}>Stance</label>
                        <select
                          id={`stance-${st.id}`}
                          value={st.stance}
                          onChange={(event) => onUpdateStatement(st.id, { stance: event.target.value as DraftStance })}
                          className="mt-1 min-h-11 border border-[#aeb8c9] bg-background px-2 text-sm"
                        >
                          {STANCES.map((stance) => (
                            <option key={stance.value} value={stance.value}>{stance.label}</option>
                          ))}
                        </select>
                      </div>
                      <div className="flex-1">
                        <label className="section-label block" htmlFor={`fol-${st.id}`}>Formal reading (FOL) — optional for now</label>
                        <input
                          id={`fol-${st.id}`}
                          value={st.fol ?? ""}
                          placeholder="null while unformalized — the statement stays, shown as pending"
                          onChange={(event) => onUpdateStatement(st.id, { fol: event.target.value.trim() ? event.target.value : null })}
                          className="mt-1 min-h-11 w-full border border-[#aeb8c9] bg-background px-2 font-code text-sm"
                        />
                      </div>
                    </div>
                  </li>
                ))}
            </ul>
          </div>
        ))}

        <button
          type="button"
          onClick={onAddDocument}
          className="transition-ui inline-flex min-h-11 items-center gap-2 self-start border border-[#8b93a2] px-4 text-sm font-semibold hover:bg-secondary"
        >
          <Plus className="size-4" aria-hidden="true" />Add a text (document)
        </button>

        {built.errors.length > 0 && (
          <ul role="alert" className="border border-[#dca497] bg-[#ffebe6] p-3 text-sm text-[#8a2d21]">
            {built.errors.map((error) => (
              <li key={error}>{error}</li>
            ))}
          </ul>
        )}
        {built.record && built.pending.length > 0 && (
          <p className="border border-[#d7ae4a] bg-[#fff0c2] p-3 text-sm text-[#694b00]">
            {built.pending.length} statement(s) have no reviewed formalization yet ({built.pending.join(", ")}):
            they stay in the record as pending — no check covers them, and nothing is dropped silently.
          </p>
        )}
      </div>
    </section>
  );
}

export function CampInputView({ workspace }: { workspace: WorkspaceData }) {
  const draft = useCampDraft();
  const built = draft.camps.map((camp) => ({ camp, built: buildRecord(camp) }));
  const ready = built.filter((entry) => entry.built.record).length;
  const pendingTotal = built.reduce((sum, entry) => sum + entry.built.pending.length, 0);

  return (
    <div className="py-8">
      <header className="max-w-3xl">
        <h1 className="text-3xl font-semibold tracking-[-0.02em]">Camps and their statements</h1>
        <p className="mt-3 text-sm leading-relaxed text-[#4c5260]">
          Paste each camp's text, name the camp, and add the statements it makes, quoting them verbatim.
          A statement without a reviewed formal reading is shown as <StatusBadge tone="amber" icon="draft">PENDING</StatusBadge> and
          stays in the record — unformalized statements are never dropped. The record JSON per camp is what the
          engine's <code className="font-code">camp</code> command and this app's camp report consume.
          {!workspace.access.reviewEnabled && " This deployment is read-only: drafting works locally, but running reports needs a reviewer token."}
        </p>
      </header>

      <p className="mt-6 border border-[#c5cbd4] bg-[#f1f2f4] p-3 text-sm text-[#3f4550]" role="status">
        {draft.camps.length} camp(s) · {draft.camps.reduce((sum, camp) => sum + camp.statements.length, 0)} statement(s) ·{" "}
        {pendingTotal} pending formalization · {ready} camp(s) with a valid record
      </p>

      <div className="mt-5 space-y-5">
        {draft.camps.map((camp) => (
          <CampCard
            key={camp.id}
            camp={camp}
            onUpdate={(patch) => draft.updateCamp(camp.id, patch)}
            onRemove={() => draft.removeCamp(camp.id)}
            onAddDocument={() => draft.addDocument(camp.id)}
            onUpdateDocument={(docId, text) => draft.updateDocument(camp.id, docId, text)}
            onRemoveDocument={(docId) => draft.removeDocument(camp.id, docId)}
            onAddStatement={(docId) => draft.addStatement(camp.id, docId)}
            onUpdateStatement={(statementId, patch) => draft.updateStatement(camp.id, statementId, patch)}
            onRemoveStatement={(statementId) => draft.removeStatement(camp.id, statementId)}
          />
        ))}
      </div>

      <button
        type="button"
        onClick={draft.addCamp}
        className="transition-ui mt-5 inline-flex min-h-11 items-center gap-2 bg-primary px-4 font-semibold text-primary-foreground hover:bg-[#173f92]"
      >
        <Plus className="size-4" aria-hidden="true" />Add a camp
      </button>
    </div>
  );
}
