"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  FileText,
  Link as LinkIcon,
  Type,
  Play,
  CheckCircle2,
  AlertTriangle,
  BookOpen,
  ListChecks,
  Download,
  ChevronDown,
  ChevronRight,
  ArrowRight,
} from "lucide-react";
import { DocAPI, DocProcessResponse, RequirementItem, ApiError } from "@/lib/api";

type InputMethod = "url" | "upload" | "paste";
type ProcessingStep = "idle" | "extracting" | "analyzing" | "done" | "error";

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

export default function DocProcessor() {
  const router = useRouter();
  const fileInputRef = useRef<HTMLInputElement>(null);

  const [inputMethod, setInputMethod] = useState<InputMethod>("url");
  const [inputValue, setInputValue] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [step, setStep] = useState<ProcessingStep>("idle");
  const [errorMsg, setErrorMsg] = useState("");
  const [result, setResult] = useState<DocProcessResponse | null>(null);
  const [expandedCategories, setExpandedCategories] = useState<Set<string>>(new Set());

  const toggleCategory = (cat: string) => {
    setExpandedCategories((prev) => {
      const next = new Set(prev);
      next.has(cat) ? next.delete(cat) : next.add(cat);
      return next;
    });
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMsg("");
    setResult(null);

    const formData = new FormData();

    if (inputMethod === "url") {
      if (!inputValue.trim()) return;
      formData.append("url", inputValue.trim());
    } else if (inputMethod === "upload") {
      if (!selectedFile) return;
      formData.append("file", selectedFile);
    } else {
      if (!inputValue.trim()) return;
      formData.append("text", inputValue.trim());
    }

    try {
      setStep("extracting");
      // The backend transitions through extracting → analyzing internally,
      // but we simulate the two-step UX on the client side.
      setTimeout(() => setStep("analyzing"), 1500);

      const data = await DocAPI.process(formData);
      setResult(data);
      setStep("done");

      // Expand all non-empty categories by default
      if (data.output) {
        const nonEmpty = Object.entries(data.output.implementation_requirements)
          .filter(([, items]) => items.length > 0)
          .map(([cat]) => cat);
        setExpandedCategories(new Set(nonEmpty));
      }
    } catch (err) {
      setStep("error");
      if (err instanceof ApiError) {
        setErrorMsg(err.message);
      } else {
        setErrorMsg("An unexpected error occurred. Is the backend running?");
      }
    }
  };

  const handleExportJSON = () => {
    if (!result || !result.output) return;
    const blob = new Blob([JSON.stringify(result.output, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `doc-analysis-${result.session.id.slice(0, 8)}.json`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const handleExportMarkdown = () => {
    if (!result || !result.output) return;
    const { output } = result;
    let md = `# Document Analysis\n\n`;
    md += `**Word Count:** ${output.word_count}\n\n`;
    md += `## Structured Summary\n\n${output.structured_summary}\n\n`;
    md += `## Product Description\n\n${output.product_description}\n\n`;
    md += `## Implementation Requirements\n\n`;

    for (const [category, items] of Object.entries(output.implementation_requirements)) {
      if (items.length === 0) continue;
      md += `### ${CATEGORY_LABELS[category] || category}\n\n`;
      for (const item of items) {
        md += `- **[${item.priority}]** ${item.requirement} _(${item.id}, confidence: ${(item.confidence * 100).toFixed(0)}%)_\n`;
      }
      md += `\n`;
    }

    const blob = new Blob([md], { type: "text/markdown" });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `doc-analysis-${result.session.id.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const totalRequirements = result?.output
    ? Object.values(result.output.implementation_requirements).reduce((sum, arr) => sum + arr.length, 0)
    : 0;

  // ─────── RENDER ───────

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      {/* Header */}
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Analyze Document</h1>
        <p className="text-[var(--text-secondary)] mt-1">
          Extract structured requirements and product descriptions from Google Docs or Word files.
        </p>
      </div>

      {/* ─── INPUT FORM ─── */}
      {step !== "done" && (
        <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-hidden">
          {/* Tabs */}
          <div className="flex border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
            {(
              [
                { key: "url", icon: LinkIcon, label: "Google Doc URL" },
                { key: "upload", icon: FileText, label: "Upload .docx" },
                { key: "paste", icon: Type, label: "Paste Text" },
              ] as const
            ).map(({ key, icon: Icon, label }) => (
              <button
                key={key}
                onClick={() => {
                  setInputMethod(key);
                  setInputValue("");
                  setSelectedFile(null);
                }}
                disabled={step !== "idle" && step !== "error"}
                className={`flex-1 py-3 text-sm font-medium transition-colors ${
                  inputMethod === key
                    ? "text-[var(--accent)] border-b-2 border-[var(--accent)]"
                    : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
                } disabled:opacity-50`}
              >
                <div className="flex items-center justify-center gap-2">
                  <Icon className="w-4 h-4" /> {label}
                </div>
              </button>
            ))}
          </div>

          <form onSubmit={handleSubmit} className="p-6">
            {inputMethod === "url" && (
              <div className="space-y-4">
                <label className="block text-sm font-medium text-[var(--text-primary)]">Document URL</label>
                <input
                  type="url"
                  required
                  placeholder="https://docs.google.com/document/d/..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  disabled={step !== "idle" && step !== "error"}
                  className="w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-md px-4 py-2 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] disabled:opacity-50"
                />
              </div>
            )}

            {inputMethod === "upload" && (
              <div className="space-y-4">
                <input
                  ref={fileInputRef}
                  type="file"
                  accept=".docx"
                  className="hidden"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] ?? null)}
                />
                <div
                  onClick={() => fileInputRef.current?.click()}
                  className="border-2 border-dashed border-[var(--border-subtle)] rounded-md p-12 text-center hover:border-[var(--accent)] transition-colors cursor-pointer"
                >
                  <FileText className="w-8 h-8 mx-auto text-[var(--text-muted)] mb-3" />
                  {selectedFile ? (
                    <>
                      <p className="text-[var(--text-primary)] font-medium">{selectedFile.name}</p>
                      <p className="text-[var(--text-secondary)] text-sm mt-1">
                        {(selectedFile.size / 1024).toFixed(1)} KB — Click to change
                      </p>
                    </>
                  ) : (
                    <>
                      <p className="text-[var(--text-primary)] font-medium">Click or drag to upload .docx</p>
                      <p className="text-[var(--text-secondary)] text-sm mt-1">Max file size: 10MB</p>
                    </>
                  )}
                </div>
              </div>
            )}

            {inputMethod === "paste" && (
              <div className="space-y-4">
                <label className="block text-sm font-medium text-[var(--text-primary)]">Raw Text</label>
                <textarea
                  required
                  rows={8}
                  placeholder="Paste your document text here..."
                  value={inputValue}
                  onChange={(e) => setInputValue(e.target.value)}
                  disabled={step !== "idle" && step !== "error"}
                  className="w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-md px-4 py-3 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] font-mono text-sm disabled:opacity-50"
                />
              </div>
            )}

            {/* Error Banner */}
            {step === "error" && errorMsg && (
              <div className="mt-4 flex items-start gap-3 p-4 rounded-lg bg-[var(--danger)]/10 border border-[var(--danger)]/20 text-[var(--danger)]">
                <AlertTriangle className="w-5 h-5 mt-0.5 flex-shrink-0" />
                <div className="text-sm">{errorMsg}</div>
              </div>
            )}

            {/* Progress Bar */}
            {(step === "extracting" || step === "analyzing") && (
              <div className="mt-6 space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-5 h-5 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
                  <span className="text-sm text-[var(--text-secondary)]">
                    {step === "extracting" ? "Extracting text from source…" : "Running NLP analysis pipeline…"}
                  </span>
                </div>
                <div className="w-full bg-[var(--bg-elevated)] rounded-full h-1.5 overflow-hidden">
                  <div
                    className="h-full bg-[var(--accent)] rounded-full transition-all duration-1000"
                    style={{ width: step === "extracting" ? "35%" : "75%" }}
                  />
                </div>
              </div>
            )}

            <div className="mt-8 flex justify-end">
              <button
                type="submit"
                disabled={step === "extracting" || step === "analyzing"}
                className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-6 py-2.5 rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {step === "extracting" || step === "analyzing" ? (
                  <>
                    <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                    Processing…
                  </>
                ) : (
                  <>
                    <Play className="w-4 h-4 fill-current" />
                    Analyze Document
                  </>
                )}
              </button>
            </div>
          </form>
        </div>
      )}

      {/* ─── RESULTS ─── */}
      {step === "done" && result && result.output && (
        <div className="space-y-6 animate-in fade-in duration-500">
          {/* Success Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <div className="p-2 rounded-lg bg-[var(--success)]/10">
                <CheckCircle2 className="w-6 h-6 text-[var(--success)]" />
              </div>
              <div>
                <h2 className="text-xl font-bold">Analysis Complete</h2>
                <p className="text-sm text-[var(--text-secondary)]">
                  {result.output.word_count.toLocaleString()} words • {totalRequirements} requirements extracted
                </p>
              </div>
            </div>
            <div className="flex items-center gap-2">
              <button
                onClick={handleExportJSON}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium border border-[var(--border-subtle)] rounded-md bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-colors"
              >
                <Download className="w-4 h-4" /> JSON
              </button>
              <button
                onClick={handleExportMarkdown}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium border border-[var(--border-subtle)] rounded-md bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:border-[var(--border-strong)] transition-colors"
              >
                <Download className="w-4 h-4" /> Markdown
              </button>
              <button
                onClick={() => {
                  setStep("idle");
                  setResult(null);
                  setInputValue("");
                  setSelectedFile(null);
                }}
                className="flex items-center gap-2 px-4 py-2 text-sm font-medium bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white rounded-md transition-colors"
              >
                <ArrowRight className="w-4 h-4" /> New Analysis
              </button>
            </div>
          </div>

          {/* Session Meta Bar */}
          <div className="flex items-center gap-4 text-xs text-[var(--text-muted)] bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-lg px-4 py-2.5">
            <span>Session: <code className="text-[var(--text-secondary)]">{result.session.id.slice(0, 8)}</code></span>
            <span>•</span>
            <span>Input: <span className="text-[var(--text-secondary)] capitalize">{result.session.input_type.replace("_", " ")}</span></span>
            <span>•</span>
            <span>Status: <span className="text-[var(--success)] font-semibold">{result.session.status}</span></span>
          </div>

          {/* Summary Card */}
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-6 py-4 border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]/50">
              <BookOpen className="w-5 h-5 text-[var(--text-secondary)]" />
              <h3 className="font-semibold">Structured Summary</h3>
            </div>
            <div className="p-6 text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
              {result.output.structured_summary}
            </div>
          </div>

          {/* Product Description Card */}
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-6 py-4 border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]/50">
              <FileText className="w-5 h-5 text-[var(--text-secondary)]" />
              <h3 className="font-semibold">Product Description</h3>
            </div>
            <div className="p-6 text-sm text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
              {result.output.product_description}
            </div>
          </div>

          {/* Requirements Card */}
          <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-hidden">
            <div className="flex items-center gap-2 px-6 py-4 border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]/50">
              <ListChecks className="w-5 h-5 text-[var(--text-secondary)]" />
              <h3 className="font-semibold">Implementation Requirements</h3>
              <span className="ml-auto text-xs text-[var(--text-muted)]">{totalRequirements} total</span>
            </div>
            <div className="divide-y divide-[var(--border-subtle)]">
              {Object.entries(result.output.implementation_requirements).map(([category, items]) => {
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
        </div>
      )}
    </div>
  );
}
