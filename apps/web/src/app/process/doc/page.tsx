"use client";

import { useState } from "react";
import { FileText, Link as LinkIcon, Type, Play } from "lucide-react";

type InputMethod = "url" | "upload" | "paste";

export default function DocProcessor() {
  const [inputMethod, setInputMethod] = useState<InputMethod>("url");
  const [inputValue, setInputValue] = useState("");
  const [isProcessing, setIsProcessing] = useState(false);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsProcessing(true);
    // API Integration will happen here
    setTimeout(() => setIsProcessing(false), 2000);
  };

  return (
    <div className="max-w-4xl mx-auto space-y-8">
      <div>
        <h1 className="text-3xl font-bold tracking-tight">Analyze Document</h1>
        <p className="text-[var(--text-secondary)] mt-1">
          Extract structured requirements and product descriptions from Google Docs or Word files.
        </p>
      </div>

      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-hidden">
        <div className="flex border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]">
          <button 
            onClick={() => setInputMethod("url")}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${inputMethod === "url" ? "text-[var(--accent)] border-b-2 border-[var(--accent)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}
          >
            <div className="flex items-center justify-center gap-2">
              <LinkIcon className="w-4 h-4" /> Google Doc URL
            </div>
          </button>
          <button 
            onClick={() => setInputMethod("upload")}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${inputMethod === "upload" ? "text-[var(--accent)] border-b-2 border-[var(--accent)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}
          >
            <div className="flex items-center justify-center gap-2">
              <FileText className="w-4 h-4" /> Upload .docx
            </div>
          </button>
          <button 
            onClick={() => setInputMethod("paste")}
            className={`flex-1 py-3 text-sm font-medium transition-colors ${inputMethod === "paste" ? "text-[var(--accent)] border-b-2 border-[var(--accent)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}
          >
            <div className="flex items-center justify-center gap-2">
              <Type className="w-4 h-4" /> Paste Text
            </div>
          </button>
        </div>

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
                className="w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-md px-4 py-2 text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)]"
              />
            </div>
          )}

          {inputMethod === "upload" && (
            <div className="space-y-4">
              <div className="border-2 border-dashed border-[var(--border-subtle)] rounded-md p-12 text-center hover:border-[var(--accent)] transition-colors cursor-pointer">
                <FileText className="w-8 h-8 mx-auto text-[var(--text-muted)] mb-3" />
                <p className="text-[var(--text-primary)] font-medium">Click or drag to upload .docx</p>
                <p className="text-[var(--text-secondary)] text-sm mt-1">Max file size: 10MB</p>
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
                className="w-full bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-md px-4 py-3 text-[var(--text-primary)] focus:outline-none focus:border-[var(--accent)] focus:ring-1 focus:ring-[var(--accent)] font-mono text-sm"
              />
            </div>
          )}

          <div className="mt-8 flex justify-end">
            <button 
              type="submit" 
              disabled={isProcessing}
              className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-6 py-2.5 rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isProcessing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Processing...
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
    </div>
  );
}
