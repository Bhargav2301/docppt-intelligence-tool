"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import { Presentation, ShieldAlert, Play, AlertCircle } from "lucide-react";
import { PptAPI, ApiError } from "@/lib/api";

type Sensitivity = "conservative" | "balanced" | "aggressive";
type ProcessStep = "idle" | "validating" | "extracting" | "analyzing" | "rewriting" | "error";

const STEP_LABELS: Record<ProcessStep, string> = {
  idle: "",
  validating: "Validating file…",
  extracting: "Extracting slide text…",
  analyzing: "Detecting AI artifacts…",
  rewriting: "Generating rewrites…",
  error: "Processing failed",
};

import { CheckCircle2, FileSpreadsheet } from "lucide-react";

export default function PPTHumanizer() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFiles, setSelectedFiles] = useState<File[]>([]);
  const [sensitivity, setSensitivity] = useState<Sensitivity>("conservative");
  const [step, setStep] = useState<ProcessStep>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [batchResult, setBatchResult] = useState<any[] | null>(null);

  const isProcessing = !["idle", "error"].includes(step);

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
    const formData = new FormData();
    formData.append("sensitivity", sensitivity);

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

  const sensitivityOptions: {
    key: Sensitivity;
    title: string;
    desc: string;
  }[] = [
    {
      key: "conservative",
      title: "Conservative",
      desc: "Only fixes obvious artifacts and markdown.",
    },
    {
      key: "balanced",
      title: "Balanced",
      desc: "Artifacts plus moderate style improvements.",
    },
    {
      key: "aggressive",
      title: "Aggressive",
      desc: "Broad rewrites and aggressive AI-style removal.",
    },
  ];

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Humanize PPT</h1>
        <p className="text-[var(--text-secondary)] mt-1">
          Detect AI artifacts and humanize slide text while perfectly preserving
          layout and formatting. Upload multiple files to humanize presentations in a batch.
        </p>
      </div>

      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6">
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* 1. Upload */}
          <div className="space-y-4">
            <h3 className="font-semibold flex items-center gap-2">
              <Presentation className="w-5 h-5 text-[var(--text-secondary)]" />
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
              className="border-2 border-dashed border-[var(--border-subtle)] rounded-md p-12 text-center hover:border-[var(--accent)] transition-colors cursor-pointer bg-[var(--bg-elevated)]"
            >
              <Presentation className="w-8 h-8 mx-auto text-[var(--text-muted)] mb-3" />
              {selectedFiles.length > 0 ? (
                <div className="space-y-2">
                  <p className="text-[var(--text-primary)] font-semibold">
                    Selected {selectedFiles.length} presentation(s):
                  </p>
                  <div className="text-[var(--text-secondary)] text-sm max-h-32 overflow-y-auto space-y-1 max-w-md mx-auto px-4 py-2 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-md">
                    {selectedFiles.map((f, i) => (
                      <div key={i} className="truncate text-left">• {f.name}</div>
                    ))}
                  </div>
                </div>
              ) : (
                <>
                  <p className="text-[var(--text-primary)] font-medium">
                    Click or drag to upload .pptx file(s)
                  </p>
                  <p className="text-[var(--text-secondary)] text-sm mt-1">
                    Max file size: 20MB • Multi-select supported
                  </p>
                </>
              )}
            </div>
          </div>

          {/* 2. Sensitivity */}
          <div className="space-y-4">
            <h3 className="font-semibold flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-[var(--text-secondary)]" />
              2. Cleanup Sensitivity
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              {sensitivityOptions.map((opt) => (
                <label
                  key={opt.key}
                  className={`border rounded-lg p-4 cursor-pointer transition-colors ${
                    sensitivity === opt.key
                      ? "border-[var(--accent)] bg-[var(--accent)]/5"
                      : "border-[var(--border-subtle)] bg-[var(--bg-elevated)] hover:border-[var(--border-strong)]"
                  }`}
                >
                  <input
                    type="radio"
                    name="sensitivity"
                    value={opt.key}
                    checked={sensitivity === opt.key}
                    onChange={() => setSensitivity(opt.key)}
                    className="sr-only"
                  />
                  <h4
                    className={`font-medium mb-1 ${
                      sensitivity === opt.key
                        ? "text-[var(--accent)]"
                        : "text-[var(--text-primary)]"
                    }`}
                  >
                    {opt.title}
                  </h4>
                  <p className="text-xs text-[var(--text-secondary)]">
                    {opt.desc}
                  </p>
                </label>
              ))}
            </div>
          </div>

          {/* Progress / Error */}
          {step !== "idle" && (
            <div className="flex items-center gap-3 p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
              {step === "error" ? (
                <AlertCircle className="w-5 h-5 text-[var(--danger)] flex-shrink-0" />
              ) : (
                <div className="w-5 h-5 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin flex-shrink-0" />
              )}
              <span
                className={`text-sm font-medium ${
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
          <div className="pt-4 border-t border-[var(--border-subtle)] flex justify-between items-center">
            <div className="text-sm text-[var(--text-muted)]">
              Files are processed locally. No external APIs used.
            </div>
            <button
              type="submit"
              disabled={isProcessing || selectedFiles.length === 0}
              className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-6 py-2.5 rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
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
                className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] hover:border-[var(--accent)] transition-all p-5 rounded-xl flex flex-col justify-between"
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
                      <span className="text-[var(--text-muted)]">Status:</span>
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
                        <span className="text-[var(--text-muted)]">Slides Count:</span>
                        <span className="text-[var(--text-primary)]">{item.total_slides} slides</span>
                      </div>
                    )}

                    {item.total_flags !== undefined && (
                      <div className="flex items-center justify-between text-sm">
                        <span className="text-[var(--text-muted)]">Detected Flags:</span>
                        <span className={`px-2 py-0.5 rounded text-xs font-semibold ${
                          item.total_flags > 0 ? "bg-[var(--warning)]/10 text-[var(--warning)]" : "bg-[var(--success)]/10 text-[var(--success)]"
                        }`}>
                          {item.total_flags} flags
                        </span>
                      </div>
                    )}

                    {item.error && (
                      <div className="text-xs text-[var(--danger)] bg-[var(--danger)]/5 border border-[var(--danger)]/15 rounded p-2 mt-2 leading-relaxed">
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
