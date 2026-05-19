"use client";

import { useState, useEffect, use } from "react";
import Link from "next/link";
import {
  Check,
  X,
  Edit2,
  AlertTriangle,
  Presentation,
  Download,
  Loader2,
  ArrowLeft,
  AlertCircle,
  ChevronRight,
  Save,
  RotateCcw,
} from "lucide-react";
import {
  SessionAPI,
  PptAPI,
  PptSegmentData,
  CompileModification,
  ApiError,
} from "@/lib/api";

type SegmentState = PptSegmentData & {
  localDecision: "pending" | "accepted" | "rejected" | "edited";
  editedText: string;
};

export default function PPTReview({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const [isLoading, setIsLoading] = useState(true);
  const [error, setError] = useState("");
  const [sessionLabel, setSessionLabel] = useState("");
  const [totalSlides, setTotalSlides] = useState(0);
  const [totalFlags, setTotalFlags] = useState(0);
  const [slides, setSlides] = useState<Record<string, SegmentState[]>>({});
  const [activeSlide, setActiveSlide] = useState<string>("");
  const [isExporting, setIsExporting] = useState(false);
  const [editingSegId, setEditingSegId] = useState<string | null>(null);

  useEffect(() => {
    SessionAPI.getDetail(id)
      .then((res) => {
        setSessionLabel(res.session.input_label || "Untitled PPT");
        if (res.session.session_type === "ppt" && res.output) {
          const pptOut = res.output as any;
          setTotalSlides(pptOut.total_slides || 0);
          setTotalFlags(pptOut.total_flags || 0);

          const slidesMap: Record<string, SegmentState[]> = {};
          const rawSlides = pptOut.slides || {};
          for (const [slideIdx, segs] of Object.entries(rawSlides)) {
            slidesMap[slideIdx] = (segs as PptSegmentData[]).map((seg) => ({
              ...seg,
              localDecision:
                seg.decision === "no_change" ? "accepted" : "pending",
              editedText: seg.final_text || seg.original_text,
            }));
          }
          setSlides(slidesMap);

          const keys = Object.keys(slidesMap).sort(
            (a, b) => Number(a) - Number(b)
          );
          if (keys.length > 0) setActiveSlide(keys[0]);
        }
      })
      .catch((e) => setError(e.message || "Failed to load session."))
      .finally(() => setIsLoading(false));
  }, [id]);

  const activeSegments = slides[activeSlide] || [];
  const flaggedSegments = activeSegments.filter(
    (s) => s.flags && s.flags.length > 0
  );

  const allSegments = Object.values(slides).flat();
  const acceptedCount = allSegments.filter(
    (s) => s.localDecision === "accepted" || s.localDecision === "edited"
  ).length;
  const pendingCount = allSegments.filter(
    (s) => s.localDecision === "pending"
  ).length;

  const setSegDecision = (
    segId: string,
    decision: SegmentState["localDecision"],
    editedText?: string
  ) => {
    setSlides((prev) => {
      const next = { ...prev };
      for (const key of Object.keys(next)) {
        next[key] = next[key].map((seg) => {
          if (seg.id === segId) {
            return {
              ...seg,
              localDecision: decision,
              editedText: editedText ?? seg.editedText,
            };
          }
          return seg;
        });
      }
      return next;
    });
  };

  const handleAcceptAll = () => {
    setSlides((prev) => {
      const next = { ...prev };
      for (const key of Object.keys(next)) {
        next[key] = next[key].map((seg) => ({
          ...seg,
          localDecision:
            seg.localDecision === "rejected" ? "rejected" : "accepted",
        }));
      }
      return next;
    });
  };

  const handleExport = async () => {
    setIsExporting(true);
    try {
      const modifications: CompileModification[] = [];
      for (const segs of Object.values(slides)) {
        for (const seg of segs) {
          if (
            seg.localDecision === "accepted" ||
            seg.localDecision === "edited"
          ) {
            const newText =
              seg.localDecision === "edited"
                ? seg.editedText
                : seg.final_text;
            if (newText && newText !== seg.original_text) {
              modifications.push({
                slide_index: seg.slide_index,
                shape_id: seg.shape_id,
                paragraph_index: seg.paragraph_index,
                run_index: seg.run_index,
                new_text: newText,
              });
            }
          }
        }
      }

      const blob = await PptAPI.compileSession(id, modifications);
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = `cleaned_${id.slice(0, 8)}.pptx`;
      a.click();
      URL.revokeObjectURL(url);
    } catch (err) {
      alert(
        err instanceof ApiError
          ? err.message
          : "Failed to compile. Check console."
      );
    } finally {
      setIsExporting(false);
    }
  };

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-[60vh]">
        <Loader2 className="w-8 h-8 text-[var(--accent)] animate-spin" />
      </div>
    );
  }

  if (error) {
    return (
      <div className="max-w-4xl mx-auto mt-16 text-center space-y-4">
        <AlertCircle className="w-12 h-12 text-[var(--danger)] mx-auto" />
        <h2 className="text-xl font-semibold">Session Not Found</h2>
        <p className="text-[var(--text-secondary)]">{typeof error === "string" ? error : JSON.stringify(error)}</p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 text-[var(--accent)] hover:underline"
        >
          <ArrowLeft className="w-4 h-4" /> Dashboard
        </Link>
      </div>
    );
  }

  const slideKeys = Object.keys(slides).sort(
    (a, b) => Number(a) - Number(b)
  );

  return (
    <div className="max-w-7xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-4 flex-shrink-0">
        <div>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 text-sm text-[var(--text-secondary)] hover:text-[var(--accent)] mb-2 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Dashboard
          </Link>
          <h1 className="text-2xl font-bold tracking-tight">{sessionLabel}</h1>
          <div className="flex items-center gap-4 mt-1 text-sm text-[var(--text-muted)]">
            <span>{totalSlides} slides</span>
            <span>•</span>
            <span>{totalFlags} flags</span>
            <span>•</span>
            <span className="text-[var(--success)]">
              {acceptedCount} accepted
            </span>
            <span>•</span>
            <span className="text-[var(--warning)]">
              {pendingCount} pending
            </span>
          </div>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={handleAcceptAll}
            className="flex items-center gap-2 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--text-primary)] px-4 py-2 rounded-md border border-[var(--border-subtle)] hover:border-[var(--border-strong)] transition-colors"
          >
            <Check className="w-4 h-4" /> Accept All
          </button>
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-5 py-2 rounded-md font-medium transition-colors disabled:opacity-50"
          >
            {isExporting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <Download className="w-4 h-4" />
            )}
            Export Clean PPT
          </button>
        </div>
      </div>

      {/* Main Panel */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-4 min-h-0">
        {/* Slide Nav */}
        <div className="md:col-span-3 lg:col-span-2 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-y-auto">
          <div className="p-3 border-b border-[var(--border-subtle)] sticky top-0 bg-[var(--bg-surface)] z-10">
            <h2 className="font-semibold text-sm text-[var(--text-primary)] flex items-center gap-2">
              <Presentation className="w-4 h-4" />
              Slides ({slideKeys.length})
            </h2>
          </div>
          <div className="p-1.5 space-y-0.5">
            {slideKeys.map((key) => {
              const segs = slides[key];
              const flagCount = segs.filter(
                (s) => s.flags && s.flags.length > 0
              ).length;
              const pendCount = segs.filter(
                (s) => s.localDecision === "pending"
              ).length;
              return (
                <button
                  key={key}
                  onClick={() => setActiveSlide(key)}
                  className={`w-full text-left px-3 py-2.5 rounded-lg text-sm font-medium transition-colors flex items-center justify-between ${
                    activeSlide === key
                      ? "bg-[var(--accent)]/10 text-[var(--accent)]"
                      : "text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)]"
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <ChevronRight
                      className={`w-3 h-3 transition-transform ${
                        activeSlide === key ? "rotate-90" : ""
                      }`}
                    />
                    Slide {Number(key) + 1}
                  </span>
                  <div className="flex items-center gap-1.5">
                    {pendCount > 0 && (
                      <span className="w-2 h-2 rounded-full bg-[var(--warning)]" />
                    )}
                    {flagCount > 0 && (
                      <span className="text-xs text-[var(--text-muted)]">
                        {flagCount}
                      </span>
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Segment Cards */}
        <div className="md:col-span-9 lg:col-span-10 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl flex flex-col min-h-0">
          <div className="p-4 border-b border-[var(--border-subtle)] flex-shrink-0 flex items-center justify-between">
            <h2 className="text-lg font-bold">
              Slide {Number(activeSlide) + 1}
            </h2>
            <span className="text-sm text-[var(--text-muted)]">
              {flaggedSegments.length} flagged segment
              {flaggedSegments.length !== 1 ? "s" : ""}
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {flaggedSegments.length === 0 ? (
              <div className="text-center py-16 text-[var(--text-muted)]">
                <Check className="w-10 h-10 mx-auto mb-3 opacity-40" />
                <p>No flagged segments on this slide.</p>
              </div>
            ) : (
              flaggedSegments.map((seg) => (
                <SegmentCard
                  key={seg.id}
                  seg={seg}
                  isEditing={editingSegId === seg.id}
                  onStartEdit={() => setEditingSegId(seg.id)}
                  onCancelEdit={() => setEditingSegId(null)}
                  onAccept={() => setSegDecision(seg.id, "accepted")}
                  onReject={() => setSegDecision(seg.id, "rejected")}
                  onSaveEdit={(text) => {
                    setSegDecision(seg.id, "edited", text);
                    setEditingSegId(null);
                  }}
                  onReset={() => setSegDecision(seg.id, "pending")}
                />
              ))
            )}
          </div>
        </div>
      </div>
    </div>
  );
}

/* ================================================================
   Segment Card — individual diff card with accept/reject/edit
   ================================================================ */

function SegmentCard({
  seg,
  isEditing,
  onStartEdit,
  onCancelEdit,
  onAccept,
  onReject,
  onSaveEdit,
  onReset,
}: {
  seg: SegmentState;
  isEditing: boolean;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onAccept: () => void;
  onReject: () => void;
  onSaveEdit: (text: string) => void;
  onReset: () => void;
}) {
  const [editText, setEditText] = useState(seg.editedText);

  const severityColor = (severity: string) => {
    switch (severity) {
      case "high":
        return "bg-[var(--danger)]/10 text-[var(--danger)] border-[var(--danger)]/20";
      case "medium":
        return "bg-[var(--warning)]/10 text-[var(--warning)] border-[var(--warning)]/20";
      default:
        return "bg-[var(--info)]/10 text-[var(--info)] border-[var(--info)]/20";
    }
  };

  const decisionBorder = () => {
    switch (seg.localDecision) {
      case "accepted":
      case "edited":
        return "border-[var(--success)]/40";
      case "rejected":
        return "border-[var(--danger)]/40 opacity-60";
      default:
        return "border-[var(--border-subtle)]";
    }
  };

  const hasRewrite =
    seg.final_text &&
    seg.final_text !== seg.original_text;

  return (
    <div
      className={`border rounded-xl p-5 bg-[var(--bg-elevated)]/30 transition-all ${decisionBorder()}`}
    >
      {/* Flags + Actions */}
      <div className="flex items-start justify-between mb-3">
        <div className="flex flex-wrap gap-2">
          {seg.flags.map((flag, i) => (
            <span
              key={i}
              className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold border ${severityColor(
                flag.severity
              )}`}
              title={flag.explanation}
            >
              <AlertTriangle className="w-3 h-3" />
              {flag.type.replace(/_/g, " ")}
            </span>
          ))}
          {seg.localDecision !== "pending" && (
            <span
              className={`px-2.5 py-1 rounded-md text-xs font-semibold border ${
                seg.localDecision === "rejected"
                  ? "bg-[var(--danger)]/10 text-[var(--danger)] border-[var(--danger)]/20"
                  : "bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/20"
              }`}
            >
              {seg.localDecision === "edited"
                ? "Edited"
                : seg.localDecision.charAt(0).toUpperCase() +
                  seg.localDecision.slice(1)}
            </span>
          )}
        </div>
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {seg.localDecision !== "pending" ? (
            <button
              onClick={onReset}
              className="p-1.5 text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] rounded-md transition-colors"
              title="Reset"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          ) : (
            <>
              {hasRewrite && (
                <button
                  onClick={onStartEdit}
                  className="p-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] rounded-md transition-colors"
                  title="Edit rewrite"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={onReject}
                className="p-1.5 text-[var(--danger)] hover:bg-[var(--danger)]/10 rounded-md transition-colors"
                title="Reject (keep original)"
              >
                <X className="w-4 h-4" />
              </button>
              <button
                onClick={onAccept}
                className="p-1.5 text-[var(--success)] hover:bg-[var(--success)]/10 rounded-md transition-colors"
                title="Accept suggested change"
              >
                <Check className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Diff View */}
      {isEditing ? (
        <div className="space-y-3">
          <div>
            <h4 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
              Original
            </h4>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              {seg.original_text}
            </p>
          </div>
          <div>
            <h4 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
              Your Edit
            </h4>
            <textarea
              value={editText}
              onChange={(e) => setEditText(e.target.value)}
              rows={3}
              className="w-full bg-[var(--bg-base)] border border-[var(--accent)] rounded-md px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)]"
            />
            <div className="flex justify-end gap-2 mt-2">
              <button
                onClick={onCancelEdit}
                className="text-sm text-[var(--text-secondary)] hover:text-[var(--text-primary)] px-3 py-1 rounded-md border border-[var(--border-subtle)]"
              >
                Cancel
              </button>
              <button
                onClick={() => onSaveEdit(editText)}
                className="flex items-center gap-1.5 text-sm font-medium bg-[var(--accent)] text-white px-3 py-1 rounded-md"
              >
                <Save className="w-3.5 h-3.5" /> Save
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          <div>
            <h4 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
              Original
            </h4>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              {seg.original_text}
            </p>
          </div>
          <div>
            <h4 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
              {seg.localDecision === "edited"
                ? "Your Edit"
                : "Suggested Rewrite"}
            </h4>
            <p className="text-sm text-[var(--text-primary)] leading-relaxed">
              {seg.localDecision === "edited"
                ? seg.editedText
                : seg.final_text || seg.original_text}
            </p>
          </div>
        </div>
      )}

      {/* Eval info */}
      {seg.eval_scores?.similarity !== undefined && (
        <div className="mt-3 pt-3 border-t border-[var(--border-subtle)] text-xs text-[var(--text-muted)]">
          Similarity: {(seg.eval_scores.similarity * 100).toFixed(1)}%
        </div>
      )}
    </div>
  );
}
