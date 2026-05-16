"use client";

import { useEffect, useState, use } from "react";
import Link from "next/link";
import {
  ArrowLeft,
  BookOpen,
  FileText,
  ListChecks,
  Download,
  ChevronDown,
  ChevronRight,
  AlertTriangle,
  Clock,
} from "lucide-react";
import { SessionAPI, DocProcessResponse, RequirementItem } from "@/lib/api";

const PRIORITY_COLORS: Record<string, { bg: string; text: string; border: string }> = {
  P0: { bg: "bg-[var(--danger)]/10", text: "text-[var(--danger)]", border: "border-[var(--danger)]/20" },
  P1: { bg: "bg-[var(--warning)]/10", text: "text-[var(--warning)]", border: "border-[var(--warning)]/20" },
  P2: { bg: "bg-[var(--info)]/10", text: "text-[var(--info)]", border: "border-[var(--info)]/20" },
};

const CATEGORY_LABELS: Record<string, string> = {
  functional: "Functional",
  technical: "Technical",
  ui_ux: "UI / UX",
  integrations: "Integrations",
  data: "Data",
  security_privacy: "Security & Privacy",
  non_functional: "Non-Functional",
};

export default function SessionDetail({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);

  const [data, setData] = useState<DocProcessResponse | null>(null);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  const toggleCategory = (cat: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      next.has(cat) ? next.delete(cat) : next.add(cat);
      return next;
    });
  };

  useEffect(() => {
    (async () => {
      try {
        setIsLoading(true);
        const result = await SessionAPI.getDetail(id);
        setData(result);
        if (result.output) {
          const nonEmpty = Object.entries(result.output.implementation_requirements)
            .filter(([, items]) => items.length > 0)
            .map(([cat]) => cat);
          setExpandedCategories(new Set(nonEmpty));
        }
      } catch {
        setError("Failed to load session. It may have been deleted.");
      } finally {
        setIsLoading(false);
      }
    })();
  }, [id]);

  const totalRequirements = data?.output
    ? Object.values(data.output.implementation_requirements).reduce((sum, arr) => sum + arr.length, 0)
    : 0;

  const handleExportJSON = () => {
    if (!data?.output) return;
    const blob = new Blob([JSON.stringify(data.output, null, 2)], { type: "application/json" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `session-${id.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  if (isLoading) {
    return (
      <div className="flex justify-center items-center min-h-[60vh]">
        <div className="w-8 h-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
      </div>
    );
  }

  if (error || !data) {
    return (
      <div className="max-w-3xl mx-auto text-center py-20">
        <AlertTriangle className="w-12 h-12 text-[var(--danger)] mx-auto mb-4" />
        <h2 className="text-xl font-bold mb-2">Session Not Found</h2>
        <p className="text-[var(--text-secondary)] mb-6">{error}</p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 px-4 py-2 bg-[var(--accent)] text-white rounded-md font-medium"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-4">
          <Link
            href="/dashboard"
            className="p-2 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] rounded-md transition-colors"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-2xl font-bold tracking-tight">
              {data.session.input_label || "Untitled Document"}
            </h1>
            <div className="flex items-center gap-3 text-xs text-[var(--text-muted)] mt-1">
              <span className="capitalize">{data.session.input_type.replace("_", " ")}</span>
              <span>•</span>
              <span className="flex items-center gap-1">
                <Clock className="w-3 h-3" />
                {data.session.created_at ? new Date(data.session.created_at).toLocaleString() : "—"}
              </span>
              <span>•</span>
              <span className="text-[var(--success)] font-semibold capitalize">{data.session.status}</span>
            </div>
          </div>
        </div>

        {data.output && (
          <button
            onClick={handleExportJSON}
            className="flex items-center gap-2 px-4 py-2 text-sm font-medium border border-[var(--border-subtle)] rounded-md bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-colors"
          >
            <Download className="w-4 h-4" /> Export JSON
          </button>
        )}
      </div>

      {/* No Output */}
      {!data.output && (
        <div className="text-center py-16 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl">
          <AlertTriangle className="w-10 h-10 text-[var(--warning)] mx-auto mb-3" />
          <p className="text-[var(--text-secondary)]">No output available for this session.</p>
          {data.session.error_message && (
            <p className="text-sm text-[var(--danger)] mt-2">{data.session.error_message}</p>
          )}
        </div>
      )}

      {/* Output Panels */}
      {data.output && (
        <>
          {/* Stats Bar */}
          <div className="flex items-center gap-6 text-sm bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-lg px-5 py-3">
            <div>
              <span className="text-[var(--text-muted)]">Words: </span>
              <span className="font-semibold text-[var(--text-primary)]">{data.output.word_count?.toLocaleString()}</span>
            </div>
            <div>
              <span className="text-[var(--text-muted)]">Requirements: </span>
              <span className="font-semibold text-[var(--text-primary)]">{totalRequirements}</span>
            </div>
          </div>

          {/* Summary */}
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-6 py-4 border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]/50">
              <BookOpen className="w-5 h-5 text-[var(--text-secondary)]" />
              <h3 className="font-semibold">Structured Summary</h3>
            </div>
            <div className="p-6 text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
              {data.output.structured_summary}
            </div>
          </div>

          {/* Product Description */}
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-6 py-4 border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]/50">
              <FileText className="w-5 h-5 text-[var(--text-secondary)]" />
              <h3 className="font-semibold">Product Description</h3>
            </div>
            <div className="p-6 text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
              {data.output.product_description}
            </div>
          </div>

          {/* Requirements */}
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-6 py-4 border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]/50">
              <ListChecks className="w-5 h-5 text-[var(--text-secondary)]" />
              <h3 className="font-semibold">Implementation Requirements</h3>
              <span className="ml-auto text-xs text-[var(--text-muted)]">{totalRequirements} total</span>
            </div>
            <div className="divide-y divide-[var(--border-subtle)]">
              {Object.entries(data.output.implementation_requirements).map(([category, items]) => {
                if (items.length === 0) return null;
                const isExpanded = expandedCategories.has(category);
                return (
                  <div key={category}>
                    <button
                      onClick={() => toggleCategory(category)}
                      className="w-full flex items-center justify-between px-6 py-3.5 text-left hover:bg-[var(--bg-elevated)] transition-colors"
                    >
                      <div className="flex items-center gap-3">
                        {isExpanded ? (
                          <ChevronDown className="w-4 h-4 text-[var(--text-muted)]" />
                        ) : (
                          <ChevronRight className="w-4 h-4 text-[var(--text-muted)]" />
                        )}
                        <span className="font-medium text-sm">{CATEGORY_LABELS[category] || category}</span>
                      </div>
                      <span className="text-xs text-[var(--text-muted)] bg-[var(--bg-elevated)] px-2 py-0.5 rounded-full">
                        {items.length}
                      </span>
                    </button>

                    {isExpanded && (
                      <div className="px-6 pb-4 space-y-2">
                        {items.map((item: RequirementItem) => {
                          const pColor = PRIORITY_COLORS[item.priority] || PRIORITY_COLORS.P2;
                          return (
                            <div
                              key={item.id}
                              className="flex items-start gap-3 p-3 rounded-lg bg-[var(--bg-elevated)]/50 border border-[var(--border-subtle)]"
                            >
                              <span
                                className={`inline-flex items-center px-2 py-0.5 rounded text-xs font-bold ${pColor.bg} ${pColor.text} border ${pColor.border}`}
                              >
                                {item.priority}
                              </span>
                              <div className="flex-1 min-w-0">
                                <p className="text-sm text-[var(--text-primary)]">{item.requirement}</p>
                                <p className="text-xs text-[var(--text-muted)] mt-1">
                                  {item.id} • Confidence: {(item.confidence * 100).toFixed(0)}%
                                </p>
                              </div>
                            </div>
                          );
                        })}
                      </div>
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </>
      )}
    </div>
  );
}
