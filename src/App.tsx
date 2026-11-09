import { useState } from "react";
import { BookOpen, Braces, Check, Download, FlaskConical, RefreshCw, Scale, ShieldCheck } from "lucide-react";
import { useWorkspace } from "@/hooks/useWorkspace";
import { DebateView } from "@/components/DebateView";
import { ProofLab } from "@/components/ProofLab";
import { EvidenceView } from "@/components/EvidenceView";
import { MethodView } from "@/components/MethodView";
import { StatementDialog } from "@/components/StatementDialog";
import { ReviewerAccess } from "@/components/ReviewerAccess";

const views = [
  { id: "debate", label: "Debate", icon: Scale },
  { id: "proofs", label: "Proof lab", icon: FlaskConical },
  { id: "evidence", label: "Evidence", icon: BookOpen },
  { id: "method", label: "Method", icon: Braces },
] as const;

type ViewId = (typeof views)[number]["id"];

export default function App() {
  const workspaceQuery = useWorkspace();
  const [view, setView] = useState<ViewId>("debate");
  const [selectedStatementId, setSelectedStatementId] = useState<string | null>(null);
  const [selectedProofId, setSelectedProofId] = useState("proof-advocate");
  const [exported, setExported] = useState(false);
  const workspace = workspaceQuery.data;

  function openProof(proofId: string) {
    setSelectedProofId(proofId);
    setSelectedStatementId(null);
    setView("proofs");
    window.scrollTo({ top: 0, behavior: "smooth" });
  }

  function exportAudit() {
    if (!workspace) return;
    const audit = {
      schema: "common-ground-audit-v1",
      application: "Common Ground",
      exportedAt: new Date().toISOString(),
      guarantee: "Conditional deductions only; source truth, values, and semantic fidelity remain subject to review.",
      workspace,
    };
    const blob = new Blob([JSON.stringify(audit, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const anchor = document.createElement("a");
    anchor.href = url;
    anchor.download = "common-ground-audit.json";
    anchor.click();
    URL.revokeObjectURL(url);
    setExported(true);
    window.setTimeout(() => setExported(false), 2500);
  }

  return (
    <div className="min-h-screen bg-background">
      <a href="#main-content" className="fixed left-3 top-3 z-[100] -translate-y-24 bg-primary px-4 py-2 font-semibold text-primary-foreground focus:translate-y-0">Skip to content</a>
      <div className="border-b border-[#bfc6d2] bg-[#1f1f1f] text-[#f8f8f8]">
        <div className="content-wrap flex min-h-9 items-center justify-between gap-4 py-1.5 text-xs">
          <span className="font-code tracking-wide">ARGUMENT INTEGRITY / WORKED PROTOTYPE</span>
          <span className="hidden items-center gap-2 text-[#d7dce5] sm:flex"><ShieldCheck className="size-3.5 text-[#c3ff00]" aria-hidden="true" /> Conditional proof, not political truth</span>
        </div>
      </div>

      <header className="border-b border-[#bfc6d2] bg-background">
        <div className="content-wrap flex flex-col gap-5 py-5 md:flex-row md:items-center md:justify-between">
          <button type="button" onClick={() => setView("debate")} className="flex items-center gap-3 self-start text-left" aria-label="Common Ground home">
            <span className="flex size-10 items-center justify-center bg-primary font-display text-lg font-bold tracking-[-0.08em] text-primary-foreground">CG</span>
            <span>
              <span className="block font-display text-xl font-semibold leading-none tracking-[-0.035em]">Common Ground</span>
              <span className="mt-1 block text-xs text-[#4c5260]">A public reason laboratory</span>
            </span>
          </button>
          <div className="flex flex-col gap-2 sm:flex-row">
          <ReviewerAccess access={workspace?.access} />
          <button
            type="button"
            onClick={exportAudit}
            disabled={!workspace}
            className="transition-ui inline-flex min-h-11 items-center justify-center gap-2 border border-[#8b93a2] px-4 text-sm font-semibold hover:bg-secondary disabled:opacity-45"
          >
            {exported ? <Check className="size-4 text-primary" aria-hidden="true" /> : <Download className="size-4" aria-hidden="true" />}
            {exported ? "Audit exported" : "Export JSON audit"}
          </button>
          </div>
        </div>
        <nav className="content-wrap grid grid-cols-2 border-t border-[#d5d9df] sm:grid-cols-4" aria-label="Workspace views">
          {views.map((item) => (
            <button
              type="button"
              key={item.id}
              onClick={() => setView(item.id)}
              aria-current={view === item.id ? "page" : undefined}
              className={`transition-ui flex min-h-14 items-center justify-center gap-2 border-b-4 px-2 text-sm font-semibold sm:justify-start sm:px-4 ${view === item.id ? "border-primary bg-[#eaf0ff] text-primary" : "border-transparent text-[#4c5260] hover:bg-secondary"}`}
            >
              <item.icon className="size-4" aria-hidden="true" />{item.label}
            </button>
          ))}
        </nav>
      </header>

      <main id="main-content" className="content-wrap">
        {workspaceQuery.isPending && (
          <div className="py-20" role="status">
            <div className="section-label text-primary">Opening the workspace</div>
            <h1 className="mt-3 text-3xl font-semibold">Loading sourced arguments and certificates…</h1>
            <div className="mt-8 grid gap-3" aria-hidden="true">
              <div className="h-5 w-2/3 animate-pulse bg-[#dfe4ec]" />
              <div className="h-5 w-full animate-pulse bg-[#dfe4ec]" />
              <div className="h-5 w-4/5 animate-pulse bg-[#dfe4ec]" />
            </div>
          </div>
        )}

        {workspaceQuery.isError && (
          <div className="my-16 border-l-4 border-[#a43b2c] bg-[#ffebe6] p-6 text-[#8a2d21]" role="alert">
            <h1 className="text-2xl font-semibold">The workspace could not be loaded.</h1>
            <p className="mt-2 text-sm">{workspaceQuery.error.message}</p>
            <button type="button" onClick={() => workspaceQuery.refetch()} className="mt-5 inline-flex min-h-11 items-center gap-2 border border-[#a43b2c] px-4 font-semibold">
              <RefreshCw className="size-4" aria-hidden="true" /> Retry
            </button>
          </div>
        )}

        {workspace && (
          <>
            <div className={view === "debate" ? undefined : "hidden"}><DebateView workspace={workspace} onOpenStatement={setSelectedStatementId} onOpenProof={openProof} /></div>
            <div className={view === "proofs" ? undefined : "hidden"}><ProofLab key={selectedProofId} workspace={workspace} selectedProofId={selectedProofId} onSelectProof={setSelectedProofId} onOpenStatement={setSelectedStatementId} /></div>
            <div className={view === "evidence" ? undefined : "hidden"}><EvidenceView workspace={workspace} /></div>
            <div className={view === "method" ? undefined : "hidden"}><MethodView workspace={workspace} /></div>
            <StatementDialog
              key={selectedStatementId ?? "closed"}
              statement={workspace.statements.find((statement) => statement.id === selectedStatementId)}
              workspace={workspace}
              open={Boolean(selectedStatementId)}
              onOpenChange={(open) => { if (!open) setSelectedStatementId(null); }}
              onOpenProof={openProof}
            />
          </>
        )}
      </main>

      <footer className="border-t border-[#bfc6d2] bg-[#f0f2f5]">
        <div className="content-wrap flex flex-col gap-3 py-6 text-xs text-[#4c5260] sm:flex-row sm:items-center sm:justify-between">
          <p>Common Ground · source-grounded argument reconstruction · Lean 4</p>
          <p>Review meanings. Check deductions. Keep disagreements visible.</p>
        </div>
      </footer>
    </div>
  );
}
