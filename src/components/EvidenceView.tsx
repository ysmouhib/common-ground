import { useMemo, useState } from "react";
import { ArrowUpRight, BookOpenCheck, Search } from "lucide-react";
import type { Evidence, WorkspaceData } from "@/hooks/useWorkspace";
import { StatusBadge } from "./Status";

const sourceLabels: Record<Evidence["sourceType"], string> = {
  peer_reviewed: "Peer-reviewed study",
  advocacy_report: "Advocacy report",
  government_report: "Government report",
  news_analysis: "News analysis",
  debate_collection: "Debate collection",
};

const filters = [
  { id: "all", label: "All sources" },
  { id: "research", label: "Studies & reports" },
  { id: "argument", label: "Debate & analysis" },
] as const;

export function EvidenceView({ workspace }: { workspace: WorkspaceData }) {
  const [filter, setFilter] = useState<(typeof filters)[number]["id"]>("all");
  const [query, setQuery] = useState("");

  const visible = useMemo(() => {
    const normalized = query.trim().toLowerCase();
    return workspace.evidence.filter((item) => {
      const inFilter =
        filter === "all" ||
        (filter === "research" && ["peer_reviewed", "advocacy_report", "government_report"].includes(item.sourceType)) ||
        (filter === "argument" && ["news_analysis", "debate_collection"].includes(item.sourceType));
      const inSearch =
        !normalized ||
        `${item.title} ${item.publisher} ${item.finding} ${item.limitation}`.toLowerCase().includes(normalized);
      return inFilter && inSearch;
    });
  }, [workspace.evidence, filter, query]);

  return (
    <div className="py-8 lg:py-10">
      <section className="grid gap-6 border-b border-[#bfc6d2] pb-8 lg:grid-cols-[1.35fr_.65fr] lg:gap-16">
        <div>
          <div className="section-label flex items-center gap-2 text-primary"><BookOpenCheck className="size-4" aria-hidden="true" /> Evidence ledger</div>
          <h1 className="mt-2 text-4xl font-semibold tracking-[-0.035em]">A citation is not a truth stamp.</h1>
          <p className="mt-3 max-w-3xl text-[#4c5260]">
            Each record keeps the supporting finding and its limitations together. Formal deductions can use an empirical premise without hiding uncertainty about the underlying source.
          </p>
        </div>
        <dl className="grid grid-cols-2 gap-4 self-end">
          <div><dt className="section-label">Records</dt><dd className="mt-1 font-display text-3xl font-semibold">{workspace.evidence.length}</dd></div>
          <div><dt className="section-label">Peer-reviewed</dt><dd className="mt-1 font-display text-3xl font-semibold">{workspace.evidence.filter((item) => item.sourceType === "peer_reviewed").length}</dd></div>
        </dl>
      </section>

      <section aria-label="Evidence filters" className="flex flex-col gap-4 py-6 md:flex-row md:items-center md:justify-between">
        <div className="flex flex-wrap gap-2" role="group" aria-label="Filter by source type">
          {filters.map((item) => (
            <button
              type="button"
              key={item.id}
              aria-pressed={filter === item.id}
              onClick={() => setFilter(item.id)}
              className={`transition-ui min-h-11 border px-4 text-sm font-semibold ${filter === item.id ? "border-primary bg-primary text-primary-foreground" : "border-[#aeb8c9] hover:bg-secondary"}`}
            >
              {item.label}
            </button>
          ))}
        </div>
        <div className="relative md:w-80">
          <Search className="pointer-events-none absolute left-3 top-3.5 size-4 text-[#596373]" aria-hidden="true" />
          <label htmlFor="evidence-search" className="sr-only">Search evidence</label>
          <input
            id="evidence-search"
            type="search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
            placeholder="Search findings or limits"
            className="min-h-11 w-full border border-[#aeb8c9] bg-background py-2 pl-10 pr-3 text-base placeholder:text-[#606a78]"
          />
        </div>
      </section>

      <p role="status" className="mb-3 text-sm text-[#4c5260]">Showing {visible.length} of {workspace.evidence.length} records.</p>
      <div className="border-t-4 border-primary">
        {visible.map((item) => (
          <article key={item.id} className="grid gap-5 border-b border-[#c8cfdb] py-7 lg:grid-cols-[.8fr_1.2fr] lg:gap-12">
            <div>
              <div className="flex flex-wrap items-center gap-2">
                <span className="font-code text-xs font-semibold text-primary">{item.id}</span>
                <StatusBadge tone={item.sourceType === "peer_reviewed" ? "green" : "blue"}>{sourceLabels[item.sourceType]}</StatusBadge>
              </div>
              <h2 className="mt-3 text-2xl font-semibold leading-tight">{item.title}</h2>
              <p className="mt-2 text-sm text-[#4c5260]">{item.authors}</p>
              <p className="mt-1 text-sm font-medium">{item.publisher} · {item.publishedAt}</p>
              <a
                href={item.url}
                target="_blank"
                rel="noreferrer"
                className="mt-4 inline-flex min-h-11 items-center gap-2 font-semibold text-primary underline underline-offset-4"
              >
                Open original source <ArrowUpRight className="size-4" aria-hidden="true" />
              </a>
            </div>
            <div>
              <h3 className="section-label">Imported finding</h3>
              <p className="mt-2 leading-relaxed">{item.finding}</p>
              <blockquote className="mt-4 border-y border-[#c8cfdb] py-4 text-lg leading-relaxed text-[#374151]">
                “{item.excerpt}”
              </blockquote>
              <div className="mt-4 bg-[#fff0c2] p-4 text-[#694b00]">
                <h3 className="section-label">Scope & limitation</h3>
                <p className="mt-2 text-sm leading-relaxed">{item.limitation}</p>
              </div>
            </div>
          </article>
        ))}
      </div>
      {visible.length === 0 && (
        <div className="border-b border-[#c8cfdb] py-12 text-center">
          <h2 className="text-xl font-semibold">No evidence matches these filters.</h2>
          <button
            type="button"
            onClick={() => { setFilter("all"); setQuery(""); }}
            className="transition-ui mt-4 min-h-11 border border-primary px-4 font-semibold text-primary hover:bg-secondary"
          >
            Clear filters
          </button>
        </div>
      )}
    </div>
  );
}
