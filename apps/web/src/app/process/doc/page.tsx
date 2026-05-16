"use client";

import { useState, useRef } from "react";
import { useRouter } from "next/navigation";
import {
  FileText,
  Link as LinkIcon,
  Type,
  Play,
  AlertCircle,
  CheckCircle2,
  ChevronDown,
  ChevronUp,
  Download,
  BookOpen,
  List,
  Lightbulb,
} from "lucide-react";
import { DocAPI, DocProcessResponse, ApiError } from "@/lib/api";

type InputMethod = "url" | "upload" | "paste";

type ProcessingStep = "idle" | "validating" | "extracting" | "analyzing" | "completed" | "error";

const STEP_LABELS: Record<ProcessingStep, string> = {
  idle: "",
  validating: "Validating input…",
  extracting: "Extracting text…",
  analyzing: "Analyzing content with NLP models…",
  completed: "Analysis complete",
  error: "Processing failed",
};

export default function DocProcessor() {
  const router = useRouter();
  const [inputMethod, setInputMethod] = useState<InputMethod>("url");
  const [inputValue, setInputValue] = useState("");
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [step, setStep] = useState<ProcessingStep>("idle");
  const [errorMessage, setErrorMessage] = useState("");
  const [result, setResult] = useState<DocProcessResponse | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const isProcessing = !["idle", "completed", "error"].includes(step);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setErrorMessage("");
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
      setStep("validating");
      // Short delay so the user sees the validating state
      await new Promise((r) => setTimeout(r, 300));
      setStep("extracting");
      await new Promise((r) => setTimeout(r, 200));
      setStep("analyzing");

      const data = await DocAPI.process(formData);
      setResult(data);
      setStep("completed");
    } catch (err) {
      setStep("error");
      if (err instanceof ApiError) {
        setErrorMessage(err.message);
      } else {
        setErrorMessage("An unexpected error occurred.");
      }
    }
  };

  const handleFileChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const file = e.target.files?.[0];
    if (file) setSelectedFile(file);
  };

  const handleExportJSON = () => {
    if (!result) return;
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
    if (!result) return;
    const o = result.output;
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
    a.download = `doc-analysis-${result.session.id.slice(0, 8)}.md`;
    a.click();
    URL.revokeObjectURL(url);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Analyze Document</h1>
        <p className="text-[var(--text-secondary)] mt-1">
          Extract structured requirements and product descriptions from Google
          Docs or Word files.
        </p>
      </div>

      {/* ───── Input Card ───── */}
      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-hidden">
        {/* Tabs */}
        <div className="flex border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
          {(
            [
              { key: "url" as const, icon: LinkIcon, label: "Google Doc URL" },
              { key: "upload" as const, icon: FileText, label: "Upload .docx" },
              { key: "paste" as const, icon: Type, label: "Paste Text" },
            ] as const
          ).map(({ key, icon: Icon, label }) => (
            <button
              key={key}
              onClick={() => {
                setInputMethod(key);
                setInputValue("");
                setSelectedFile(null);
              }}
              className={`flex-1 py-3 text-sm font-medium transition-colors ${
                inputMethod === key
                  ? "text-[var(--accent)] border-b-2 border-[var(--accent)]"
                  : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"
              }`}
            >
              <div className="flex items-center justify-center gap-2">
                <Icon className="w-4 h-4" /> {label}
              </div>
            </button>
          ))}
        </div>

        {/* Form */}
        <form onSubmit={handleSubmit} className="p-6">
          {inputMethod === "url" && (
            <div className="space-y-4">
              <label className="block text-sm font-medium text-[var(--text-primary)]">
                Document URL
              </label>
              <input
                type="url"
                required
                placeholder="https://docs.google.com/document/d/..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                className="w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-md px-4 py-2 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]"
              />
            </div>
          )}

          {inputMethod === "upload" && (
            <div className="space-y-4">
              <input
                ref={fileInputRef}
                type="file"
                accept=".docx"
                onChange={handleFileChange}
                className="hidden"
              />
              <div
                onClick={() => fileInputRef.current?.click()}
                className="border-2 border-dashed border-[var(--border-subtle)] rounded-md p-12 text-center hover:border-[var(--accent)] transition-colors cursor-pointer"
              >
                <FileText className="w-8 h-8 mx-auto text-[var(--text-muted)] mb-3" />
                {selectedFile ? (
                  <p className="text-[var(--text-primary)] font-medium">
                    {selectedFile.name}
                  </p>
                ) : (
                  <>
                    <p className="text-[var(--text-primary)] font-medium">
                      Click or drag to upload .docx
                    </p>
                    <p className="text-[var(--text-secondary)] text-sm mt-1">
                      Max file size: 10MB
                    </p>
                  </>
                )}
              </div>
            </div>
          )}

          {inputMethod === "paste" && (
            <div className="space-y-4">
              <label className="block text-sm font-medium text-[var(--text-primary)]">
                Raw Text
              </label>
              <textarea
                required
                rows={8}
                placeholder="Paste your document text here..."
                value={inputValue}
                onChange={(e) => setInputValue(e.target.value)}
                className="w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-md px-4 py-3 text-[var(--text-primary)] placeholder:text-[var(--text-muted)] focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] font-mono text-sm"
              />
            </div>
          )}

          {/* ── Progress / Error Bar ── */}
          {step !== "idle" && step !== "completed" && (
            <div className="mt-6 flex items-center gap-3 p-4 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
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

          {/* ── Submit ── */}
          <div className="mt-8 flex justify-end">
            <button
              type="submit"
              disabled={isProcessing}
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
                  Analyze Document
                </>
              )}
            </button>
          </div>
        </form>
      </div>

      {/* ───── Results ───── */}
      {result && <ResultsPanel result={result} onExportJSON={handleExportJSON} onExportMarkdown={handleExportMarkdown} />}
    </div>
  );
}

/* ================================================================
   Results Panel — renders after successful /api/doc/process call
   ================================================================ */

function ResultsPanel({
  result,
  onExportJSON,
  onExportMarkdown,
}: {
  result: DocProcessResponse;
  onExportJSON: () => void;
  onExportMarkdown: () => void;
}) {
  const [expandedSections, setExpandedSections] = useState<Record<string, boolean>>({
    summary: true,
    product: true,
    requirements: true,
  });

  const toggle = (key: string) =>
    setExpandedSections((prev) => ({ ...prev, [key]: !prev[key] }));

  const o = result.output;
  const s = result.session;

  const getPriorityColor = (priority: string) => {
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
  };

  return (
    <div className="space-y-6 animate-in fade-in slide-in-from-bottom-4 duration-500">
      {/* Header Bar */}
      <div className="flex items-center justify-between p-4 bg-[var(--bg-surface)] border border-[var(--success)]/30 rounded-xl">
        <div className="flex items-center gap-3">
          <CheckCircle2 className="w-5 h-5 text-[var(--success)]" />
          <div>
            <span className="font-semibold text-[var(--text-primary)]">
              Analysis Complete
            </span>
            <span className="text-sm text-[var(--text-muted)] ml-3">
              {o.word_count} words • Session {s.id.slice(0, 8)}
            </span>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={onExportJSON}
            className="flex items-center gap-1.5 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--accent)] px-3 py-1.5 rounded-md border border-[var(--border-subtle)] hover:border-[var(--accent)] transition-colors"
          >
            <Download className="w-3.5 h-3.5" /> JSON
          </button>
          <button
            onClick={onExportMarkdown}
            className="flex items-center gap-1.5 text-sm font-medium text-[var(--text-secondary)] hover:text-[var(--accent)] px-3 py-1.5 rounded-md border border-[var(--border-subtle)] hover:border-[var(--accent)] transition-colors"
          >
            <Download className="w-3.5 h-3.5" /> Markdown
          </button>
        </div>
      </div>

      {/* Structured Summary */}
      <CollapsibleSection
        title="Structured Summary"
        icon={<BookOpen className="w-5 h-5 text-blue-400" />}
        isOpen={expandedSections.summary}
        onToggle={() => toggle("summary")}
      >
        <div className="prose prose-invert prose-sm max-w-none text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
          {o.structured_summary}
        </div>
      </CollapsibleSection>

      {/* Product Description */}
      <CollapsibleSection
        title="Product Description"
        icon={<Lightbulb className="w-5 h-5 text-amber-400" />}
        isOpen={expandedSections.product}
        onToggle={() => toggle("product")}
      >
        <div className="prose prose-invert prose-sm max-w-none text-[var(--text-secondary)] leading-relaxed whitespace-pre-wrap">
          {o.product_description}
        </div>
      </CollapsibleSection>

      {/* Implementation Requirements */}
      <CollapsibleSection
        title="Implementation Requirements"
        icon={<List className="w-5 h-5 text-[var(--accent)]" />}
        isOpen={expandedSections.requirements}
        onToggle={() => toggle("requirements")}
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
                            <span
                              className={`px-2 py-0.5 rounded text-xs font-semibold border whitespace-nowrap ${getPriorityColor(
                                priority
                              )}`}
                            >
                              {priority}
                            </span>
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
      </CollapsibleSection>
    </div>
  );
}

/* ================================================================
   Collapsible Section — reusable accordion wrapper
   ================================================================ */

function CollapsibleSection({
  title,
  icon,
  isOpen,
  onToggle,
  children,
}: {
  title: string;
  icon: React.ReactNode;
  isOpen: boolean;
  onToggle: () => void;
  children: React.ReactNode;
}) {
  return (
    <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-hidden">
      <button
        onClick={onToggle}
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
