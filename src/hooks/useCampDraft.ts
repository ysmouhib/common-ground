import { useCallback, useState } from "react";

/**
 * Local draft state for the camp input view (CG6-2): camps with pasted texts
 * (documents) and statements quoted verbatim from them. Everything here is
 * client-side; running a report on a record is reviewer-gated (CG6-1a/1b).
 */

export type DraftStance = "endorsed" | "rejected_firm" | "rejected_soft";

export const STANCES: { value: DraftStance; label: string }[] = [
  { value: "endorsed", label: "Endorsed" },
  { value: "rejected_firm", label: "Rejected (firm)" },
  { value: "rejected_soft", label: "Rejected (soft)" },
];

export interface DraftDocument {
  id: string;
  text: string;
}

export interface DraftStatement {
  id: string;
  documentId: string;
  quote: string;
  stance: DraftStance;
  fol: string | null;
}

export interface DraftCamp {
  id: string;
  name: string;
  documents: DraftDocument[];
  statements: DraftStatement[];
}

export interface RecordBuild {
  record: {
    camp: string;
    documents: { id: string; text: string }[];
    statements: {
      id: string;
      stance: DraftStance;
      fol: string | null;
      document: string;
      quote: string;
      span: [number, number];
    }[];
  } | null;
  errors: string[];
  /** Ids of statements without a reviewed formalization: pending, never dropped. */
  pending: string[];
}

let counter = 0;
function nextId(prefix: string): string {
  counter += 1;
  return `${prefix}-${counter.toString(36)}${Math.random().toString(36).slice(2, 6)}`;
}

/** The same rule the API and the engine apply to a camp name (a plain directory name). */
export function campNameError(name: string): string | null {
  if (!name || name !== name.trim()) return "The camp name must be non-empty text without surrounding spaces.";
  if (name.length > 64) return "The camp name must be at most 64 characters.";
  if (name === "." || name === ".." || name.endsWith(".")) return "The camp name must be a plain directory name.";
  if (/[/\\:*?"<>|]/.test(name)) return "The camp name must not contain / \\ : * ? \" < > |.";
  if ([...name].some((ch) => ch.charCodeAt(0) < 32)) return "The camp name must not contain control characters.";
  return null;
}

/** Build the engine record JSON for one camp, or the errors that block it. */
export function buildRecord(camp: DraftCamp): RecordBuild {
  const errors: string[] = [];
  const nameError = campNameError(camp.name);
  if (nameError) errors.push(nameError);

  const documents: { id: string; text: string }[] = [];
  const seenDocs = new Set<string>();
  for (const doc of camp.documents) {
    if (!doc.id.trim()) errors.push("Every document needs an id.");
    if (seenDocs.has(doc.id)) errors.push(`Document id "${doc.id}" repeats.`);
    seenDocs.add(doc.id);
    if (!doc.text.trim()) errors.push(`Document ${doc.id} has no text to quote from.`);
    documents.push({ id: doc.id, text: doc.text });
  }

  const byDoc = new Map(documents.map((doc) => [doc.id, doc.text]));
  const statements: NonNullable<RecordBuild["record"]>["statements"] = [];
  const seenStatements = new Set<string>();
  const pending: string[] = [];
  for (const st of camp.statements) {
    if (seenStatements.has(st.id)) errors.push(`Statement id ${st.id} repeats.`);
    seenStatements.add(st.id);
    const text = byDoc.get(st.documentId);
    if (text === undefined) {
      errors.push(`Statement ${st.id} names unknown document ${st.documentId}.`);
      continue;
    }
    if (!st.quote.trim()) {
      errors.push(`Statement ${st.id} needs its quote as text.`);
      continue;
    }
    const start = text.indexOf(st.quote);
    if (start < 0) {
      errors.push(`Statement ${st.id}: its quote is not a verbatim span of document ${st.documentId}.`);
      continue;
    }
    const fol = st.fol && st.fol.trim() ? st.fol.trim() : null;
    if (fol === null) pending.push(st.id);
    statements.push({
      id: st.id,
      stance: st.stance,
      fol,
      document: st.documentId,
      quote: st.quote,
      span: [start, start + st.quote.length],
    });
  }

  if (errors.length > 0 || documents.length === 0) {
    if (documents.length === 0) errors.push("Paste at least one text (document) per camp.");
    return { record: null, errors, pending };
  }
  return { record: { camp: camp.name, documents, statements }, errors, pending };
}

export function useCampDraft() {
  const [camps, setCamps] = useState<DraftCamp[]>([
    { id: nextId("camp"), name: "camp-a", documents: [], statements: [] },
  ]);

  const addCamp = useCallback(() => {
    setCamps((current) => [...current, { id: nextId("camp"), name: `camp-${String.fromCharCode(97 + current.length)}`, documents: [], statements: [] }]);
  }, []);

  const updateCamp = useCallback((campId: string, patch: Partial<Omit<DraftCamp, "id">>) => {
    setCamps((current) => current.map((camp) => (camp.id === campId ? { ...camp, ...patch } : camp)));
  }, []);

  const removeCamp = useCallback((campId: string) => {
    setCamps((current) => current.filter((camp) => camp.id !== campId));
  }, []);

  const addDocument = useCallback((campId: string) => {
    setCamps((current) =>
      current.map((camp) =>
        camp.id === campId
          ? { ...camp, documents: [...camp.documents, { id: nextId("doc"), text: "" }] }
          : camp,
      ),
    );
  }, []);

  const updateDocument = useCallback((campId: string, docId: string, text: string) => {
    setCamps((current) =>
      current.map((camp) =>
        camp.id === campId
          ? { ...camp, documents: camp.documents.map((doc) => (doc.id === docId ? { ...doc, text } : doc)) }
          : camp,
      ),
    );
  }, []);

  const removeDocument = useCallback((campId: string, docId: string) => {
    setCamps((current) =>
      current.map((camp) =>
        camp.id === campId
          ? {
              ...camp,
              documents: camp.documents.filter((doc) => doc.id !== docId),
              statements: camp.statements.filter((st) => st.documentId !== docId),
            }
          : camp,
      ),
    );
  }, []);

  const addStatement = useCallback((campId: string, documentId: string) => {
    setCamps((current) =>
      current.map((camp) =>
        camp.id === campId
          ? {
              ...camp,
              statements: [
                ...camp.statements,
                { id: nextId("st"), documentId, quote: "", stance: "endorsed" as DraftStance, fol: null },
              ],
            }
          : camp,
      ),
    );
  }, []);

  const updateStatement = useCallback((campId: string, statementId: string, patch: Partial<Omit<DraftStatement, "id">>) => {
    setCamps((current) =>
      current.map((camp) =>
        camp.id === campId
          ? { ...camp, statements: camp.statements.map((st) => (st.id === statementId ? { ...st, ...patch } : st)) }
          : camp,
      ),
    );
  }, []);

  const removeStatement = useCallback((campId: string, statementId: string) => {
    setCamps((current) =>
      current.map((camp) =>
        camp.id === campId ? { ...camp, statements: camp.statements.filter((st) => st.id !== statementId) } : camp,
      ),
    );
  }, []);

  return {
    camps,
    addCamp,
    updateCamp,
    removeCamp,
    addDocument,
    updateDocument,
    removeDocument,
    addStatement,
    updateStatement,
    removeStatement,
  };
}
