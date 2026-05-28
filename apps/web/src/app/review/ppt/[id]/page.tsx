/* eslint-disable */
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
  RefreshCw,
  ChevronDown,
  ChevronUp,
} from "lucide-react";
import {
  SessionAPI,
  PptAPI,
  PptSegmentData,
  CompileModification,
  ApiError,
  RewriteAPI,
  TonePreset,
  RewriteIntensity,
  PptSegmentV2,
} from "@/lib/api";
import AiLikenessBadge from "@/components/AiLikenessBadge";
import SafetyLabelBadge from "@/components/SafetyLabelBadge";

type SegmentState = PptSegmentV2 & {
  localDecision: "pending" | "accepted" | "rejected" | "edited";
  editedText: string;
};

const TONE_PRESETS = [
  { value: "presentation_concise", label: "Concise" },
  { value: "executive_polished", label: "Executive" },
  { value: "founder_clear", label: "Founder" },
  { value: "product_manager_direct", label: "Product" },
  { value: "consulting_professional", label: "Consulting" },
] as const;

const INTENSITIES = [
  { value: "minimal", label: "Minimal" },
  { value: "balanced", label: "Balanced" },
  { value: "strong", label: "Strong" },
] as const;

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
  const [slideScores, setSlideScores] = useState<Record<string, number>>({});
  const [activeSlide, setActiveSlide] = useState<string>("");
  const [isExporting, setIsExporting] = useState(false);
  const [editingSegId, setEditingSegId] = useState<string | null>(null);

  // Run Rewrite States
  const [rewriteOpen, setRewriteOpen] = useState(false);
  const [rewriteTone, setRewriteTone] = useState<TonePreset>("presentation_concise");
  const [rewriteIntensity, setRewriteIntensity] = useState<RewriteIntensity>("balanced");
  const [isRunningRewrite, setIsRunningRewrite] = useState(false);
  const [rewriteMessage, setRewriteMessage] = useState<{ status: "success" | "error"; text: string } | null>(null);

  // Safety Confirmation Modal States
  const [showExportModal, setShowExportModal] = useState(false);
  const [manualReviewCount, setManualReviewCount] = useState(0);

  useEffect(() => {
    refreshSessionData(true);
  }, [id]);

  const refreshSessionData = async (setInitialSlide = false) => {
    try {
      const res = await SessionAPI.getDetail(id);
      setSessionLabel(res.session.input_label || "Untitled PPT");
      if (res.session.session_type === "ppt" && res.output) {
        const pptOut = res.output;
        setTotalSlides(pptOut.total_slides || 0);
        setTotalFlags(pptOut.total_flags || 0);
        setSlideScores(pptOut.slide_scores || {});

        const slidesMap: Record<string, SegmentState[]> = {};
        const rawSlides = pptOut.slides || {};
        for (const [slideIdx, segs] of Object.entries(rawSlides)) {
          slidesMap[slideIdx] = (segs as PptSegmentV2[]).map((seg) => ({
            ...seg,
            localDecision:
              seg.decision === "no_change" ? "accepted" : "pending",
            editedText: seg.final_text || seg.original_text,
          }));
        }
        setSlides(slidesMap);

        if (setInitialSlide) {
          const keys = Object.keys(slidesMap).sort(
            (a, b) => Number(a) - Number(b)
          );
          if (keys.length > 0) setActiveSlide(keys[0]);
        }
      }
    } catch (e: any) {
      setError(e.message || "Failed to load session.");
    } finally {
      setIsLoading(false);
    }
  };

  const handleRunRewrite = async () => {
    setIsRunningRewrite(true);
    setRewriteMessage(null);
    try {
      const res = await RewriteAPI.run({
        session_id: id,
        tone_preset: rewriteTone,
        intensity: rewriteIntensity,
      });
      setRewriteMessage({
        status: "success",
        text: `Rewrite complete — ${res.total_rewritten} segments updated, ${res.total_passed} passed through, ${res.total_failed} failed judge.`,
      });
      await refreshSessionData(false);
    } catch (err: any) {
      setRewriteMessage({
        status: "error",
        text: err.message || "Failed to run rewrite pipeline.",
      });
    } finally {
      setIsRunningRewrite(false);
    }
  };

  const handleRerunSegment = async (segId: string) => {
    const result = await RewriteAPI.rerunSegment(id, segId, rewriteTone, rewriteIntensity);
    
    // Update local final text
    setSlides((prev) => {
      const next = { ...prev };
      for (const key of Object.keys(next)) {
        next[key] = next[key].map((seg) => {
          if (seg.id === segId) {
            return {
              ...seg,
              final_text: result.candidate_text || seg.final_text,
              editedText: result.candidate_text || seg.editedText,
            };
          }
          return seg;
        });
      }
      return next;
    });

    // Re-fetch detail in background to update likeness and safety metrics
    try {
      const detail = await SessionAPI.getDetail(id);
      if (detail.output && detail.output.slides) {
        const updatedSeg = Object.values(detail.output.slides).flat().find((s: any) => s.id === segId);
        if (updatedSeg) {
          setSlides((prev) => {
            const next = { ...prev };
            for (const key of Object.keys(next)) {
              next[key] = next[key].map((seg) => {
                if (seg.id === segId) {
                  return {
                    ...seg,
                    ai_likeness: updatedSeg.ai_likeness,
                    safety_label: updatedSeg.safety_label,
                    final_text: updatedSeg.final_text,
                    editedText: updatedSeg.final_text,
                  };
                }
                return seg;
              });
            }
            return next;
          });
        }
      }
    } catch (e) {
      console.error("Failed to background refresh likeness score:", e);
    }
  };

  const activeSegments = slides[activeSlide] || [];
  const flaggedSegments = activeSegments.filter(
    (s) => s.flags && s.flags.length > 0
  );

  const allSegments = Object.values(slides).flat();
  const totalSegments = allSegments.length;
  const acceptedEditedCount = allSegments.filter(
    (s) => s.localDecision === "accepted" || s.localDecision === "edited"
  ).length;
  const rejectedCount = allSegments.filter(
    (s) => s.localDecision === "rejected"
  ).length;
  const reviewedCount = acceptedEditedCount + rejectedCount;

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

  const executeExport = async () => {
    setShowExportModal(false);
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

  const handleExport = async () => {
    // 1. Export Pre-check Modal for manual_review items
    const manualReviewUnrejected = allSegments.filter(
      (s) => s.safety_label === "manual_review" && s.localDecision !== "rejected"
    ).length;

    if (manualReviewUnrejected > 0) {
      setManualReviewCount(manualReviewUnrejected);
      setShowExportModal(true);
    } else {
      await executeExport();
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
        <p className="text-[var(--text-secondary)]">{error}</p>
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

  const acceptedPercentage = totalSegments > 0 ? (acceptedEditedCount / totalSegments) * 100 : 0;
  const rejectedPercentage = totalSegments > 0 ? (rejectedCount / totalSegments) * 100 : 0;
  const reviewedPercentage = totalSegments > 0 ? Math.round((reviewedCount / totalSegments) * 100) : 0;

  return (
    <div className="max-w-7xl mx-auto h-[calc(100vh-8rem)] flex flex-col space-y-4">
      {/* Header Panel */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 flex-shrink-0 border-b border-[var(--border-subtle)] pb-4">
        <div>
          <Link
            href="/dashboard"
            className="inline-flex items-center gap-1.5 text-sm text-[var(--text-secondary)] hover:text-[var(--accent)] mb-1 transition-colors"
          >
            <ArrowLeft className="w-4 h-4" /> Dashboard
          </Link>
          <h1 className="text-2xl font-bold tracking-tight">{sessionLabel}</h1>
          <div className="flex items-center gap-3 mt-1.5 text-xs text-[var(--text-muted)] font-medium">
            <span>{totalSlides} slides</span>
            <span>•</span>
            <span>{totalFlags} flags</span>
          </div>
        </div>

        {/* Progress Bar & Buttons */}
        <div className="flex flex-wrap items-center gap-4">
          {/* Progress bar across all slides */}
          <div className="flex flex-col gap-1 w-44 sm:w-52">
            <div className="flex justify-between text-[10px] text-[var(--text-muted)] font-bold uppercase tracking-wider">
              <span>{reviewedPercentage}% reviewed</span>
              <span>{reviewedCount}/{totalSegments}</span>
            </div>
            <div className="h-2 w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-full overflow-hidden flex">
              <div style={{ width: `${acceptedPercentage}%` }} className="bg-teal-500 h-full transition-all" />
              <div style={{ width: `${rejectedPercentage}%` }} className="bg-red-500/40 h-full transition-all" />
            </div>
          </div>

          <button
            onClick={handleAcceptAll}
            className="flex items-center gap-1.5 text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] px-3.5 py-2.5 rounded-lg border border-[var(--border-subtle)] hover:border-[var(--border-strong)] transition-colors"
          >
            <Check className="w-4 h-4" /> Accept All
          </button>
          
          <button
            onClick={handleExport}
            disabled={isExporting}
            className="flex items-center gap-1.5 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-4 py-2.5 rounded-lg text-xs font-bold transition-all disabled:opacity-50"
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

      {/* "Run Rewrite" Panel */}
      <div className="flex-shrink-0 border border-[var(--border-subtle)] rounded-xl bg-[var(--bg-surface)] overflow-hidden shadow-sm">
        <button
          onClick={() => setRewriteOpen(!rewriteOpen)}
          className="w-full flex items-center justify-between px-5 py-3 hover:bg-[var(--bg-elevated)]/40 transition-colors"
        >
          <div className="flex items-center gap-2">
            <RefreshCw className={`w-4 h-4 text-[var(--accent)] ${isRunningRewrite ? "animate-spin" : ""}`} />
            <span className="text-sm font-semibold text-[var(--text-primary)]">Run Rewrite Options</span>
          </div>
          {rewriteOpen ? <ChevronUp className="w-4 h-4 text-[var(--text-muted)]" /> : <ChevronDown className="w-4 h-4 text-[var(--text-muted)]" />}
        </button>

        {rewriteOpen && (
          <div className="p-5 border-t border-[var(--border-subtle)] space-y-4 bg-[var(--bg-elevated)]/10">
            <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-1.5">Tone Preset</label>
                <select
                  value={rewriteTone}
                  onChange={(e) => setRewriteTone(e.target.value as TonePreset)}
                  className="w-full bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] font-medium"
                >
                  {TONE_PRESETS.map((t) => (
                    <option key={t.value} value={t.value}>
                      {t.label}
                    </option>
                  ))}
                </select>
              </div>

              <div>
                <label className="block text-xs font-bold uppercase tracking-wider text-[var(--text-muted)] mb-1.5">Intensity</label>
                <div className="flex bg-[var(--bg-surface)] p-1 rounded-lg border border-[var(--border-subtle)] w-full">
                  {INTENSITIES.map((opt) => (
                    <button
                      key={opt.value}
                      type="button"
                      onClick={() => setRewriteIntensity(opt.value)}
                      className={`flex-1 py-1.5 text-xs font-semibold rounded-md transition-all ${
                        rewriteIntensity === opt.value
                          ? "bg-[var(--accent)] text-white shadow-sm"
                          : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                      }`}
                    >
                      {opt.label}
                    </button>
                  ))}
                </div>
              </div>
            </div>

            <div className="flex items-center gap-3 pt-2">
              <button
                type="button"
                onClick={handleRunRewrite}
                disabled={isRunningRewrite}
                className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-5 py-2.5 rounded-lg text-xs font-bold transition-all disabled:opacity-50 shadow-sm"
              >
                {isRunningRewrite ? (
                  <>
                    <Loader2 className="w-3.5 h-3.5 animate-spin" />
                    Running rewrite pipeline…
                  </>
                ) : (
                  "Rewrite Flagged Segments"
                )}
              </button>

              {rewriteMessage && (
                <div className={`text-xs font-semibold px-3 py-2 rounded-lg border ${
                  rewriteMessage.status === "success" 
                    ? "bg-green-500/5 text-green-400 border-green-500/10" 
                    : "bg-red-500/5 text-red-400 border-red-500/10"
                }`}>
                  {rewriteMessage.text}
                </div>
              )}
            </div>
          </div>
        )}
      </div>

      {/* Main Split Panels */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-4 min-h-0">
        {/* Slide Nav */}
        <div className="md:col-span-3 lg:col-span-2 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-y-auto shadow-sm">
          <div className="p-3.5 border-b border-[var(--border-subtle)] sticky top-0 bg-[var(--bg-surface)] z-10">
            <h2 className="font-semibold text-xs text-[var(--text-muted)] uppercase tracking-wider flex items-center gap-2">
              <Presentation className="w-4 h-4 text-[var(--accent)]" />
              Slides ({slideKeys.length})
            </h2>
          </div>
          <div className="p-1.5 space-y-0.5">
            {slideKeys.map((key) => {
              const segs = slides[key];
              const score = slideScores[key] || 0;
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
                  className={`w-full text-left px-3 py-2.5 rounded-lg text-xs font-semibold transition-colors flex items-center justify-between ${
                    activeSlide === key
                      ? "bg-[var(--accent)]/10 text-[var(--accent)]"
                      : "text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)]/40"
                  }`}
                >
                  <span className="flex items-center gap-2">
                    <ChevronRight
                      className={`w-3.5 h-3.5 transition-transform ${
                        activeSlide === key ? "rotate-90 text-[var(--accent)]" : "text-[var(--text-muted)]"
                      }`}
                    />
                    Slide {Number(key) + 1}
                  </span>
                  
                  <div className="flex items-center gap-1.5">
                    {flagCount > 0 ? (
                      <AiLikenessBadge 
                        score={score} 
                        band={score > 60 ? "high" : score >= 25 ? "moderate" : "low"} 
                        size="sm" 
                      />
                    ) : (
                      <span className="text-green-500 font-bold text-xs" title="No flags detected">✓</span>
                    )}
                    {pendCount > 0 && (
                      <span className="w-2.5 h-2.5 rounded-full bg-[var(--warning)]" title="Pending reviews" />
                    )}
                  </div>
                </button>
              );
            })}
          </div>
        </div>

        {/* Segment Cards list */}
        <div className="md:col-span-9 lg:col-span-10 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl flex flex-col min-h-0 shadow-sm">
          <div className="p-4 border-b border-[var(--border-subtle)] flex-shrink-0 flex items-center justify-between">
            <h2 className="text-sm font-bold uppercase tracking-wider text-[var(--text-secondary)]">
              Slide {Number(activeSlide) + 1}
            </h2>
            <span className="text-xs text-[var(--text-muted)] font-semibold uppercase tracking-wider bg-[var(--bg-elevated)] px-2.5 py-1 rounded-md">
              {flaggedSegments.length} flagged segment{flaggedSegments.length !== 1 ? "s" : ""}
            </span>
          </div>

          <div className="flex-1 overflow-y-auto p-4 space-y-4">
            {flaggedSegments.length === 0 ? (
              <div className="text-center py-20 text-[var(--text-muted)]">
                <Check className="w-12 h-12 mx-auto mb-3 text-green-500 opacity-60 bg-green-500/5 p-2.5 rounded-full border border-green-500/10" />
                <p className="font-semibold text-sm">No flagged segments on this slide.</p>
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
                  onRerun={handleRerunSegment}
                />
              ))
            )}
          </div>
        </div>
      </div>

      {/* Safety Confirmation Modal */}
      {showExportModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl max-w-md w-full p-6 space-y-6 shadow-2xl animate-in scale-in">
            <div className="flex items-start gap-4">
              <div className="p-3 rounded-full bg-red-500/10 text-red-500 border border-red-500/20">
                <AlertTriangle className="w-6 h-6" />
              </div>
              <div className="space-y-2">
                <h3 className="text-lg font-bold text-[var(--text-primary)]">Export with layout risks?</h3>
                <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                  {manualReviewCount} segment{manualReviewCount !== 1 ? "s are" : " is"} flagged for manual review and may overflow their text boxes.
                </p>
                <p className="text-xs text-[var(--text-muted)] leading-relaxed">
                  Review these text blocks to prevent presentation overflow, or reject the suggested rewrites to keep original text.
                </p>
              </div>
            </div>

            <div className="flex gap-3 justify-end pt-2">
              <button
                type="button"
                onClick={() => setShowExportModal(false)}
                className="px-4 py-2 text-sm font-semibold rounded-lg border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)] transition-all"
              >
                Go Back
              </button>
              <button
                type="button"
                onClick={executeExport}
                className="px-4 py-2 text-sm font-bold rounded-lg bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white transition-all"
              >
                Export Anyway
              </button>
            </div>
          </div>
        </div>
      )}
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
  onRerun,
}: {
  seg: SegmentState;
  isEditing: boolean;
  onStartEdit: () => void;
  onCancelEdit: () => void;
  onAccept: () => void;
  onReject: () => void;
  onSaveEdit: (text: string) => void;
  onReset: () => void;
  onRerun: (segId: string) => Promise<void>;
}) {
  const [editText, setEditText] = useState(seg.editedText);
  const [isRerunning, setIsRerunning] = useState(false);

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

  const handleRerun = async () => {
    setIsRerunning(true);
    try {
      await onRerun(seg.id);
    } catch (e) {
      console.error(e);
    } finally {
      setIsRerunning(false);
    }
  };

  const hasRewrite =
    seg.final_text &&
    seg.final_text !== seg.original_text;

  // Block Accept button on manual_review layout safety
  const isAcceptBlocked = seg.safety_label === "manual_review";

  return (
    <div
      className={`border rounded-xl p-5 bg-[var(--bg-elevated)]/30 transition-all space-y-4 ${decisionBorder()}`}
    >
      {/* Role + Flags + Safety Badge + Actions */}
      <div className="flex items-start justify-between gap-4">
        <div className="flex flex-wrap items-center gap-2">
          {/* Segment Role label */}
          {seg.role && (
            <span className="text-[10px] uppercase tracking-wider font-bold text-[var(--text-muted)] bg-[var(--bg-elevated)] px-2 py-0.5 rounded border border-[var(--border-subtle)]">
              {seg.role.replace(/_/g, " ")}
            </span>
          )}

          {seg.flags.map((flag, i) => (
            <span
              key={i}
              className={`inline-flex items-center gap-1 px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wide ${severityColor(
                flag.severity
              )}`}
            >
              <AlertTriangle className="w-3 h-3 flex-shrink-0" />
              {flag.type.replace(/_/g, " ")}
            </span>
          ))}

          {/* Safety label badge */}
          {seg.safety_label && (
            <SafetyLabelBadge label={seg.safety_label} />
          )}

          {seg.localDecision !== "pending" && (
            <span
              className={`px-2 py-0.5 rounded text-[10px] font-bold border uppercase tracking-wide ${
                seg.localDecision === "rejected"
                  ? "bg-[var(--danger)]/10 text-[var(--danger)] border-[var(--danger)]/20"
                  : "bg-[var(--success)]/10 text-[var(--success)] border-[var(--success)]/20"
              }`}
            >
              {seg.localDecision === "edited"
                ? "Edited"
                : seg.localDecision}
            </span>
          )}
        </div>

        {/* Action buttons */}
        <div className="flex items-center gap-1.5 flex-shrink-0">
          {seg.localDecision !== "pending" ? (
            <button
              onClick={onReset}
              className="p-1.5 text-[var(--text-muted)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] rounded-md transition-colors"
              title="Reset Decision"
            >
              <RotateCcw className="w-4 h-4" />
            </button>
          ) : (
            <>
              {/* Re-run button */}
              {seg.flags.length > 0 && (
                <button
                  onClick={handleRerun}
                  disabled={isRerunning}
                  className="p-1.5 text-[var(--text-secondary)] hover:text-[var(--accent)] hover:bg-[var(--bg-elevated)] rounded-md transition-colors disabled:opacity-50"
                  title="Re-run segment humanizer rewrite"
                >
                  {isRerunning ? (
                    <Loader2 className="w-4 h-4 animate-spin text-[var(--accent)]" />
                  ) : (
                    <RefreshCw className="w-4 h-4" />
                  )}
                </button>
              )}

              {hasRewrite && (
                <button
                  onClick={onStartEdit}
                  disabled={isRerunning}
                  className="p-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] rounded-md transition-colors"
                  title="Edit rewrite option"
                >
                  <Edit2 className="w-4 h-4" />
                </button>
              )}

              <button
                onClick={onReject}
                disabled={isRerunning}
                className="p-1.5 text-[var(--danger)] hover:bg-[var(--danger)]/10 rounded-md transition-colors"
                title="Reject (keep original text)"
              >
                <X className="w-4 h-4" />
              </button>

              <button
                onClick={onAccept}
                disabled={isRerunning || (isAcceptBlocked && seg.localDecision === "pending")}
                className={`p-1.5 text-[var(--success)] hover:bg-[var(--success)]/10 rounded-md transition-colors disabled:opacity-50 disabled:cursor-not-allowed`}
                title={isAcceptBlocked ? "This rewrite may overflow the text box. Edit manually or reject." : "Accept rewrite suggested change"}
              >
                <Check className="w-4 h-4" />
              </button>
            </>
          )}
        </div>
      </div>

      {/* Per-segment AI-likeness score line */}
      {seg.ai_likeness && (
        <div className="text-xs text-[var(--text-secondary)] flex items-center gap-2">
          <span className="font-semibold">AI Likeness:</span>
          <AiLikenessBadge score={seg.ai_likeness.score} band={seg.ai_likeness.band} size="sm" />
          {seg.ai_likeness.reasons && seg.ai_likeness.reasons.length > 0 && (
            <span 
              className="text-[var(--text-muted)] italic truncate max-w-[400px]" 
              title={seg.ai_likeness.reasons.join(", ")}
            >
              — {seg.ai_likeness.reasons[0]}
            </span>
          )}
        </div>
      )}

      {/* "Why flagged" expandable disclosures panel */}
      {seg.flags.length > 0 && (
        <details className="text-xs border border-[var(--border-subtle)] rounded-lg p-2.5 bg-[var(--bg-base)]/40">
          <summary className="cursor-pointer font-semibold select-none text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-colors">
            Why this was flagged
          </summary>
          <div className="mt-2 space-y-2.5 pt-2 border-t border-[var(--border-subtle)]/50">
            {seg.flags.map((flag, idx) => (
              <div key={idx} className="border-l-2 border-[var(--accent)]/40 pl-3 py-0.5 space-y-1">
                <div className="font-bold text-[var(--text-primary)] uppercase text-[10px] tracking-wider">
                  {flag.type.replace(/_/g, " ")}
                </div>
                {flag.explanation && (
                  <p className="text-[var(--text-secondary)]">{flag.explanation}</p>
                )}
                {flag.matched_text && (
                  <p className="text-[var(--text-muted)] font-mono text-[10px] bg-[var(--bg-elevated)] px-1.5 py-0.5 rounded inline-block">
                    Matched: <code>{flag.matched_text}</code>
                  </p>
                )}
                {flag.recommendation && (
                  <p className="italic text-[var(--text-muted)]">Recommendation: {flag.recommendation}</p>
                )}
              </div>
            ))}
          </div>
        </details>
      )}

      {/* Diff / Text Content View */}
      {isEditing ? (
        <div className="space-y-3">
          <div>
            <h4 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-1.5">
              Original Text
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
              className="w-full bg-[var(--bg-base)] border border-[var(--accent)] rounded-lg px-3 py-2 text-sm text-[var(--text-primary)] focus:outline-none focus:ring-1 focus:ring-[var(--accent)]"
            />
            <div className="flex justify-end gap-2 mt-2">
              <button
                onClick={onCancelEdit}
                className="text-sm font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] px-3.5 py-1.5 rounded-lg border border-[var(--border-subtle)] transition-colors"
              >
                Cancel
              </button>
              <button
                onClick={() => onSaveEdit(editText)}
                className="flex items-center gap-1.5 text-sm font-bold bg-[var(--accent)] text-white px-3.5 py-1.5 rounded-lg transition-colors"
              >
                <Save className="w-3.5 h-3.5" /> Save
              </button>
            </div>
          </div>
        </div>
      ) : (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          <div className="space-y-1">
            <h4 className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
              Original Text
            </h4>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              {seg.original_text}
            </p>
          </div>
          <div className="space-y-1">
            <h4 className="text-[10px] font-bold text-[var(--text-muted)] uppercase tracking-wider">
              {seg.localDecision === "edited"
                ? "Your Edit"
                : "Suggested Rewrite"}
            </h4>
            <p className="text-sm text-[var(--text-primary)] font-medium leading-relaxed">
              {seg.localDecision === "edited"
                ? seg.editedText
                : seg.final_text || seg.original_text}
            </p>
          </div>
        </div>
      )}

      {/* Eval info metrics */}
      {seg.eval_scores?.similarity !== undefined && (
        <div className="pt-2 text-[10px] font-bold uppercase tracking-wider text-[var(--text-muted)] flex items-center gap-1">
          <span>Similarity:</span>
          <span className="text-[var(--text-secondary)]">{(seg.eval_scores.similarity * 100).toFixed(1)}%</span>
        </div>
      )}
    </div>
  );
}
