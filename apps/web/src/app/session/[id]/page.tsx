"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  BookOpen,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Download,
  AlertCircle,
  Lightbulb,
  List,
  Loader2,
} from "lucide-react";
import { SessionAPI, SessionDetailResponse, ExportAPI } from "@/lib/api";

export default function SessionDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [data, setData] = useState<SessionDetailResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    SessionAPI.getDetail(id)
      .then(setData)
      .catch((e) => setError(e.message || "Failed to load session."))
      .finally(() => setIsLoading(false));
  }, [id]);

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 text-[var(--accent)] animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-4xl mx-auto mt-16 text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-[var(--danger)] mx-auto" />
        <h2 className="text-xl font-semibold text-[var(--text-primary)]">
          Session Not Found
        </h2>
        <p className="text-[var(--text-secondary)]">{error}</p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 text-[var(--accent)] hover:underline mt-4"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>
      </div>
    );
  }

  const s = data.session;
  const o = data.output;

  const handleExportJSON = () => {
    if (!o) return;
    const blob = new Blob([JSON.stringify(o, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `doc-analysis-${s.id.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportMarkdown = () => {
    if (!o) return;
    let md = `# Document Analysis\n\n`;
    md += `## Structured Summary\n\n${o.structured_summary}\n\n`;
    md += `## Product Description\n\n${o.product_description}\n\n`;
    md += `## Implementation Requirements\n\n`;
    for (const [category, items] of Object.entries(o.implementation_requirements)) {
      md += `### ${category}\n\n`;
      if (Array.isArray(items)) {
        items.forEach((item: any) => {
          const priority = item.priority ? ` [${item.priority}]` : "";
          const text = typeof item === "string" ? item : item.text || JSON.stringify(item);
          md += `- ${text}${priority}\n`;
        });
      }
      md += "\n";
    }
    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `doc-analysis-${s.id.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      {/* Back + Header */}
      <div>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-1.5 text-sm text-[var(--text-secondary)] hover:text-[var(--accent)] mb-4 transition-colors"
        >
          <ArrowLeft className="w-4 h-4" /> Dashboard
        </Link>
        <h1 className="text-3xl font-bold tracking-tight">
          {s.input_label || "Untitled Document"}
        </h1>
        <div className="flex items-center gap-3 mt-2 text-sm text-[var(--text-muted)]">
          <span className="uppercase font-semibold tracking-wider">
            {s.session_type}
          </span>
          <span>•</span>
          <span>{s.input_type}</span>
          <span>•</span>
          <span>
            {s.created_at
              ? new Date(s.created_at).toLocaleString()
              : "Unknown time"}
          </span>
          {o && (
            <>
              <span>•</span>
              <span>{o.word_count} words</span>
            </>
          )}
        </div>
      </div>

      {/* Status Banner */}
      {s.status === "completed" && o ? (
        <div className="flex items-center justify-between p-4 bg-[var(--bg-surface)] border border-[var(--success)]/30 rounded-xl">
          <div className="flex items-center gap-3">
            <CheckCircle2 className="w-5 h-5 text-[var(--success)]" />
            <span className="font-semibold text-[var(--text-primary)]">
              Analysis Complete
            </span>
          </div>
          <div className="flex items-center gap-2">
            <button
              onClick={handleExportJSON}
              className="flex items-center gap-1.5 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--accent)] px-3 py-1.5 rounded-md border border-[var(--border-subtle)] hover:border-[var(--accent)] transition-colors"
            >
              <Download className="w-3.5 h-3.5" /> JSON
            </button>
            <button
              onClick={handleExportMarkdown}
              className="flex items-center gap-1.5 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--accent)] px-3 py-1.5 rounded-md border border-[var(--border-subtle)] hover:border-[var(--accent)] transition-colors"
            >
              <Download className="w-3.5 h-3.5" /> Markdown
            </button>
            <a
              href={ExportAPI.getPdfUrl(s.id)}
              download
              className="flex items-center gap-1.5 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--accent)] px-3 py-1.5 rounded-md border border-[var(--border-subtle)] hover:border-[var(--accent)] transition-colors"
            >
              <Download className="w-3.5 h-3.5" /> PDF
            </a>
            <a
              href={ExportAPI.getWordUrl(s.id)}
              download
              className="flex items-center gap-1.5 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--accent)] px-3 py-1.5 rounded-md border border-[var(--border-subtle)] hover:border-[var(--accent)] transition-colors"
            >
              <Download className="w-3.5 h-3.5" /> Word
            </a>
          </div>
        </div>
      ) : (
        <div className="flex items-center gap-3 p-4 bg-[var(--bg-surface)] border border-[var(--danger)]/30 rounded-xl">
          <AlertCircle className="w-5 h-5 text-[var(--danger)]" />
          <div>
            <span className="font-semibold text-[var(--text-primary)] capitalize">
              {s.status}
            </span>
            {s.error_message && (
              <p className="text-sm text-[var(--text-secondary)] mt-1">
                {s.error_message}
              </p>
            )}
          </div>
        </div>
      )}

      {/* Output Panels */}
      {o && (
        <div className="space-y-6">
          <OutputSection
            title="Structured Summary"
            icon={<BookOpen className="w-5 h-5 text-blue-400" />}
          >
            <div className="prose prose-invert prose-sm max-w-none text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
              {o.structured_summary}
            </div>
          </OutputSection>

          <OutputSection
            title="Product Description"
            icon={<Lightbulb className="w-5 h-5 text-amber-400" />}
          >
            <div className="prose prose-invert prose-sm max-w-none text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
              {o.product_description}
            </div>
          </OutputSection>

          <OutputSection
            title="Implementation Requirements"
            icon={<List className="w-5 h-5 text-[var(--accent)]" />}
          >
            <div className="space-y-6">
              {Object.entries(o.implementation_requirements).map(
                ([category, items]) => (
                  <div key={category}>
                    <h4 className="text-sm font-bold text-[var(--text-primary)] uppercase tracking-wider mb-3">
                      {category}
                    </h4>
                    {Array.isArray(items) && items.length > 0 ? (
                      <div className="space-y-2">
                        {items.map((item: any, idx: number) => {
                          const text =
                            typeof item === "string"
                              ? item
                              : item.text || JSON.stringify(item);
                          const priority =
                            typeof item === "object" ? item.priority : null;
                          return (
                            <div
                              key={idx}
                              className="flex items-start gap-3 p-3 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)]"
                            >
                              <span className="text-[var(--text-muted)] text-xs font-mono mt-0.5 select-none">
                                {String(idx + 1).padStart(2, "0")}
                              </span>
                              <span className="flex-1 text-sm text-[var(--text-primary)] leading-relaxed">
                                {text}
                              </span>
                              {priority && (
                                <PriorityBadge priority={priority} />
                              )}
                            </div>
                          );
                        })}
                      </div>
                    ) : (
                      <p className="text-sm text-[var(--text-muted)] italic">
                        No requirements extracted for this category.
                      </p>
                    )}
                  </div>
                )
              )}
            </div>
          </OutputSection>
        </div>
      )}
    </div>
  );
}

/* ── Collapsible output section ── */
function OutputSection({
  title,
  icon,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  children: React.ReactNode;
}) {
  const [isOpen, setIsOpen] = useState(true);
  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-hidden">
      <button
        onClick={() => setIsOpen(!isOpen)}
        className="w-full flex items-center justify-between px-6 py-4 hover:bg-[var(--bg-elevated)] transition-colors"
      >
        <div className="flex items-center gap-3">
          {icon}
          <h3 className="font-semibold text-[var(--text-primary)]">{title}</h3>
        </div>
        {isOpen ? (
          <ChevronUp className="w-4 h-4 text-[var(--text-muted)]" />
        ) : (
          <ChevronDown className="w-4 h-4 text-[var(--text-muted)]" />
        )}
      </button>
      {isOpen && (
        <div className="px-6 pb-6 border-t border-[var(--border-subtle)] pt-4">
          {children}
        </div>
      )}
    </div>
  );
}

/* ── Priority badge ── */
function PriorityBadge({ priority }: { priority: string }) {
  const colorClass = (() => {
    switch (priority?.toLowerCase()) {
      case "high":
      case "critical":
        return "bg-[var(--danger)]/10 text-[var(--danger)] border-[var(--danger)]/20";
      case "medium":
        return "bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/20";
      case "low":
        return "bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/20";
      default:
        return "bg-[var(--border-subtle)] text-[var(--text-secondary)] border-[var(--border-strong)]";
    }
  })();

  return (
    <span
      className={`px-2 py-0.5 rounded text-xs font-semibold border whitespace-nowrap ${colorClass}`}
    >
      {priority}
    </span>
  );
}
