/* eslint-disable */
"use client";

import { useState, useRef, useEffect } from "react";
import { useRouter } from "next/navigation";
import { Presentation, Play, AlertCircle, CheckCircle2, ShieldAlert, Sparkles, Key } from "lucide-react";
import { PptAPI, SettingsAPI, ApiError, TonePreset, RewriteIntensity } from "@/lib/api";

type ProcessStep = "idle" | "validating" | "extracting" | "analyzing" | "rewriting" | "error";

const STEP_LABELS: Record<ProcessStep, string> = {
  idle: "",
  validating: "Validating file…",
  extracting: "Extracting slide text…",
  analyzing: "Detecting AI artifacts…",
  rewriting: "Generating rewrites…",
  error: "Processing failed",
};

const TONE_PRESETS = [
  { value: "presentation_concise", label: "Concise" },
  { value: "executive_polished", label: "Executive" },
  { value: "founder_clear", label: "Founder" },
  { value: "product_manager_direct", label: "Product" },
  { value: "consulting_professional", label: "Consulting" },
] as const;

const INTENSITIES = [
  { 
    value: "minimal", 
    label: "Minimal", 
    tooltip: "Only fix clear artifacts and framing leftovers" 
  },
  { 
    value: "balanced", 
    label: "Balanced", 
    tooltip: "Improve rhythm and reduce AI-like phrasing" 
  },
  { 
    value: "strong", 
    label: "Strong", 
    tooltip: "Full compression, specificity, and tone transformation" 
  },
] as const;

export default function PPTHumanizer() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  
  const [tonePreset, setTonePreset] = useState<TonePreset>("presentation_concise");
  const [intensity, setIntensity] = useState<RewriteIntensity>("balanced");
  const [geminiKeySet, setGeminiKeySet] = useState(false);

  const [step, setStep] = useState<ProcessStep>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [batchResult, setBatchResult] = useState<any[] | null>(null);

  const isProcessing = !["idle", "error"].includes(step);

  useEffect(() => {
    // 1. Check Gemini BYOK key status
    if (typeof window !== "undefined") {
      const key = sessionStorage.getItem("gemini_api_key");
      setGeminiKeySet(!!key);
    }

    // 2. Fetch default preferences on mount
    SettingsAPI.get()
      .then((data) => {
        if (data.default_tone_preset) {
          setTonePreset(data.default_tone_preset as TonePreset);
        }
        if (data.default_intensity) {
          setIntensity(data.default_intensity as RewriteIntensity);
        }
      })
      .catch((err) => {
        console.error("Failed to load settings defaults:", err);
      });
  }, []);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const files = e.target.files;
    if (files && files.length > 0) {
      setSelectedFiles(Array.from(files));
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (selectedFiles.length === 0) return;

    setErrorMessage("");
    setBatchResult(null);

    // Persist settings preferences to user settings profile
    try {
      await SettingsAPI.update({
        default_tone_preset: tonePreset,
        default_intensity: intensity,
      });
    } catch (err) {
      console.error("Failed to save default settings:", err);
    }

    const formData = new FormData();
    formData.append("tone_preset", tonePreset);
    formData.append("intensity", intensity);

    const isBatch = selectedFiles.length > 1;

    if (isBatch) {
      selectedFiles.forEach((file) => {
        formData.append("files", file);
      });
    } else {
      formData.append("file", selectedFiles[0]);
    }

    try {
      setStep("validating");
      await new Promise((r) => setTimeout(r, 300));
      setStep("extracting");
      await new Promise((r) => setTimeout(r, 200));
      setStep("analyzing");

      if (isBatch) {
        const result = await PptAPI.batchProcess(formData);
        setBatchResult(result);
        setStep("idle");
      } else {
        const result = await PptAPI.process(formData);
        // Redirect to single review page
        router.push(`/review/ppt/${result.session.id}`);
      }
    } catch (err) {
      setStep("error");
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("An unexpected error occurred.");
      }
    }
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8 animate-fade-in">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Humanize PPT</h1>
          <p className="text-[var(--text-secondary)] mt-1">
            Detect AI artifacts and humanize slide text while perfectly preserving
            layout and formatting. Upload multiple files to humanize presentations in a batch.
          </p>
        </div>
        
        {/* Gemini BYOK key status indicator */}
        <div className="flex-shrink-0">
          {geminiKeySet ? (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-green-500/10 text-green-400 border border-green-500/20 shadow-sm shadow-green-500/5">
              ✅ Gemini key set
            </span>
          ) : (
            <span className="inline-flex items-center gap-1.5 px-3 py-1.5 rounded-full text-xs font-semibold bg-amber-500/10 text-amber-400 border border-amber-500/20 shadow-sm shadow-amber-500/5">
              ⚠️ No Gemini key — using rule-based fallback
            </span>
          )}
        </div>
      </div>

      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6 shadow-sm">
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* 1. Upload */}
          <div className="space-y-4">
            <h3 className="font-semibold text-lg flex items-center gap-2 text-[var(--text-primary)]">
              <Presentation className="w-5 h-5 text-[var(--accent)]" />
              1. Upload Presentation(s)
            </h3>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pptx"
              multiple
              onChange={handleFileChange}
              className="hidden"
            />
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-[var(--border-subtle)] rounded-xl p-12 text-center hover:border-[var(--accent)] hover:bg-[var(--bg-elevated)]/20 transition-all cursor-pointer bg-[var(--bg-elevated)]/10"
            >
              <Presentation className="w-10 h-10 mx-auto text-[var(--text-muted)] mb-3" />
              {selectedFiles.length > 0 ? (
                <div className="space-y-2">
                  <p className="text-[var(--text-primary)] font-semibold">
                    Selected {selectedFiles.length} presentation(s):
                  </p>
                  <div className="text-[var(--text-secondary)] text-sm max-h-32 overflow-y-auto space-y-1 max-w-md mx-auto px-4 py-2 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-md">
                    {selectedFiles.map((f, i) => (
                      <div key={i} className="truncate text-left font-medium">• {f.name}</div>
                    ))}
                  </div>
                </div>
              ) : (
                <>
                  <p className="text-[var(--text-primary)] font-semibold">
                    Click or drag to upload .pptx file(s)
                  </p>
                  <p className="text-[var(--text-muted)] text-sm mt-1">
                    Max file size: 50MB • Multi-select supported
                  </p>
                </>
              )}
            </div>
          </div>

          {/* 2. Tone Preset Selector */}
          <div className="space-y-4 pt-4 border-t border-[var(--border-subtle)]">
            <h3 className="font-semibold text-lg flex items-center gap-2 text-[var(--text-primary)]">
              <Sparkles className="w-5 h-5 text-[var(--accent)]" />
              2. Select Rewrite Tone Preset
            </h3>
            <div className="flex flex-wrap gap-2.5">
              {TONE_PRESETS.map((t) => (
                <button
                  key={t.value}
                  type="button"
                  onClick={() => setTonePreset(t.value)}
                  className={`px-4 py-2 rounded-full text-sm font-semibold border transition-all ${
                    tonePreset === t.value
                      ? "bg-[var(--accent)] text-white border-[var(--accent)] shadow-sm shadow-[var(--accent)]/10"
                      : "bg-[var(--bg-elevated)] text-[var(--text-secondary)] border-[var(--border-subtle)] hover:border-[var(--border-strong)]"
                  }`}
                >
                  {t.label}
                </button>
              ))}
            </div>
          </div>

          {/* 3. Intensity Selector */}
          <div className="space-y-4 pt-4 border-t border-[var(--border-subtle)]">
            <h3 className="font-semibold text-lg flex items-center gap-2 text-[var(--text-primary)]">
              <ShieldAlert className="w-5 h-5 text-[var(--accent)]" />
              3. Select Rewrite Intensity
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {INTENSITIES.map((opt) => (
                <div
                  key={opt.value}
                  onClick={() => setIntensity(opt.value)}
                  title={opt.tooltip}
                  className={`border rounded-xl p-4 cursor-pointer transition-all ${
                    intensity === opt.value
                      ? "border-[var(--accent)] bg-[var(--accent)]/5 ring-1 ring-[var(--accent)]"
                      : "border-[var(--border-subtle)] bg-[var(--bg-elevated)]/30 hover:border-[var(--border-strong)]"
                  }`}
                >
                  <h4
                    className={`font-semibold mb-1 text-sm ${
                      intensity === opt.value
                        ? "text-[var(--accent)]"
                        : "text-[var(--text-primary)]"
                    }`}
                  >
                    {opt.label}
                  </h4>
                  <p className="text-xs text-[var(--text-secondary)] leading-relaxed">
                    {opt.tooltip}
                  </p>
                </div>
              ))}
            </div>
          </div>

          {/* Progress / Error */}
          {step !== "idle" && (
            <div className="flex items-center gap-3 p-4 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-elevated)]/50 animate-pulse">
              {step === "error" ? (
                <AlertCircle className="w-5 h-5 text-[var(--danger)] flex-shrink-0" />
              ) : (
                <div className="w-5 h-5 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin flex-shrink-0" />
              )}
              <span
                className={`text-sm font-semibold ${
                  step === "error"
                    ? "text-[var(--danger)]"
                    : "text-[var(--text-primary)]"
                }`}
              >
                {step === "error" ? errorMessage : STEP_LABELS[step]}
              </span>
            </div>
          )}

          {/* Submit */}
          <div className="pt-6 border-t border-[var(--border-subtle)] flex flex-col sm:flex-row gap-4 justify-between items-center">
            <div className="text-xs text-[var(--text-muted)] font-medium">
              Files are processed securely. AI humanization uses advanced layout guards.
            </div>
            <button
              type="submit"
              disabled={isProcessing || selectedFiles.length === 0}
              className="w-full sm:w-auto flex items-center justify-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-6 py-3 rounded-lg font-bold transition-all disabled:opacity-50 disabled:cursor-not-allowed shadow-md shadow-[var(--accent)]/10"
            >
              {isProcessing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Processing…
                </>
              ) : (
                <>
                  <Play className="w-4 h-4 fill-current" />
                  Analyze & Humanize
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* ───── Batch Results Grid ───── */}
      {batchResult && (
        <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
          <div className="flex items-center justify-between p-4 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl">
            <div className="flex items-center gap-3">
              <CheckCircle2 className="w-5 h-5 text-[var(--success)]" />
              <div>
                <span className="font-semibold text-[var(--text-primary)]">
                  Presentation Batch Processed
                </span>
                <span className="text-sm text-[var(--text-muted)] ml-3">
                  Humanized {batchResult.length} slide decks
                </span>
              </div>
            </div>
          </div>

          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            {batchResult.map((item, idx) => (
              <div 
                key={idx} 
                className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--accent)] transition-all p-5 rounded-xl flex flex-col justify-between shadow-sm"
              >
                <div>
                  <div className="flex items-center gap-2 mb-3">
                    <Presentation className="w-5 h-5 text-[var(--accent)]" />
                    <h3 className="font-semibold text-[var(--text-primary)] truncate max-w-[250px]">
                      {item.filename}
                    </h3>
                  </div>

                  <div className="space-y-2 mb-4">
                    <div className="flex items-center justify-between text-sm">
                      <span className="text-[var(--text-muted)] font-medium">Status:</span>
                      <span className={`px-2 py-0.5 rounded text-xs font-semibold uppercase ${
                        item.status === "completed" 
                          ? "bg-[var(--success)]/10 text-[var(--success)] border border-[var(--success)]/20" 
                          : "bg-[var(--danger)]/10 text-[var(--danger)] border border-[var(--danger)]/20"
                      }`}>
                        {item.status === "completed" ? "Success" : "Failed"}
                      </span>
                    </div>

                    {item.total_slides !== undefined && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-[var(--text-muted)] font-medium">Slides Count:</span>
                        <span className="text-[var(--text-primary)] font-semibold">{item.total_slides} slides</span>
                      </div>
                    )}

                    {item.total_flags !== undefined && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-[var(--text-muted)] font-medium">Detected Flags:</span>
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                          item.total_flags > 0 ? "bg-[var(--warning)]/10 text-[var(--warning)]" : "bg-[var(--success)]/10 text-[var(--success)]"
                        }`}>
                          {item.total_flags} flags
                        </span>
                      </div>
                    )}

                    {item.error && (
                      <div className="text-xs text-[var(--danger)] bg-[var(--danger)]/5 border border-[var(--danger)]/15 rounded p-2.5 mt-2 leading-relaxed">
                        {item.error}
                      </div>
                    )}
                  </div>
                </div>

                {item.status === "completed" && (
                  <button
                    onClick={() => router.push(`/review/ppt/${item.session_id}`)}
                    className="w-full mt-2 text-center text-sm font-semibold text-white bg-[var(--accent)] hover:bg-[var(--accent-hover)] transition-colors py-2.5 rounded-lg"
                  >
                    Review humanized slides
                  </button>
                )}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  );
}
