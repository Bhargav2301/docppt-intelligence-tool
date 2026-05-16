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

export default function PPTHumanizer() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [sensitivity, setSensitivity] = useState<Sensitivity>("conservative");
  const [step, setStep] = useState<ProcessStep>("idle");
  const [errorMessage, setErrorMessage] = useState("");

  const isProcessing = !["idle", "error"].includes(step);

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setSelectedFile(file);
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!selectedFile) return;

    setErrorMessage("");
    const formData = new FormData();
    formData.append("file", selectedFile);
    formData.append("sensitivity", sensitivity);

    try {
      setStep("validating");
      await new Promise((r) => setTimeout(r, 300));
      setStep("extracting");
      await new Promise((r) => setTimeout(r, 200));
      setStep("analyzing");

      const result = await PptAPI.process(formData);

      // Redirect to review page
      router.push(`/review/ppt/${result.session.id}`);
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
          layout and formatting.
        </p>
      </div>

      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6">
        <form onSubmit={handleSubmit} className="space-y-8">
          {/* 1. Upload */}
          <div className="space-y-4">
            <h3 className="font-semibold flex items-center gap-2">
              <Presentation className="w-5 h-5 text-[var(--text-secondary)]" />
              1. Upload Presentation
            </h3>
            <input
              ref={fileInputRef}
              type="file"
              accept=".pptx"
              onChange={handleFileChange}
              className="hidden"
            />
            <div
              onClick={() => fileInputRef.current?.click()}
              className="border-2 border-dashed border-[var(--border-subtle)] rounded-md p-12 text-center hover:border-[var(--accent)] transition-colors cursor-pointer bg-[var(--bg-elevated)]"
            >
              <Presentation className="w-8 h-8 mx-auto text-[var(--text-muted)] mb-3" />
              {selectedFile ? (
                <p className="text-[var(--text-primary)] font-medium">
                  {selectedFile.name}
                </p>
              ) : (
                <>
                  <p className="text-[var(--text-primary)] font-medium">
                    Click or drag to upload .pptx
                  </p>
                  <p className="text-[var(--text-secondary)] text-sm mt-1">
                    Max file size: 20MB
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
              disabled={isProcessing || !selectedFile}
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
    </div>
  );
}
