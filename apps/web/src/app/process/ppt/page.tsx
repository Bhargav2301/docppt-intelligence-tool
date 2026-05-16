"use client";

import { useState } from "react";
import { Presentation, ShieldAlert, Play } from "lucide-react";

export default function PPTHumanizer() {
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
        <h1 className="text-3xl font-bold tracking-tight">Humanize PPT</h1>
        <p className="text-[var(--text-secondary)] mt-1">
          Detect AI artifacts and humanize slide text while perfectly preserving layout and formatting.
        </p>
      </div>

      <div className="bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl p-6">
        <form onSubmit={handleSubmit} className="space-y-8">
          
          <div className="space-y-4">
            <h3 className="font-semibold flex items-center gap-2">
              <Presentation className="w-5 h-5 text-[var(--text-secondary)]" />
              1. Upload Presentation
            </h3>
            <div className="border-2 border-dashed border-[var(--border-subtle)] rounded-md p-12 text-center hover:border-[var(--accent)] transition-colors cursor-pointer bg-[var(--bg-elevated)]">
              <Presentation className="w-8 h-8 mx-auto text-[var(--text-muted)] mb-3" />
              <p className="text-[var(--text-primary)] font-medium">Click or drag to upload .pptx</p>
              <p className="text-[var(--text-secondary)] text-sm mt-1">Max file size: 20MB</p>
            </div>
          </div>

          <div className="space-y-4">
            <h3 className="font-semibold flex items-center gap-2">
              <ShieldAlert className="w-5 h-5 text-[var(--text-secondary)]" />
              2. Cleanup Sensitivity
            </h3>
            <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
              <label className="border border-[var(--accent)] bg-[var(--accent)]/5 rounded-lg p-4 cursor-pointer">
                <input type="radio" name="sensitivity" value="conservative" className="sr-only" defaultChecked />
                <h4 className="font-medium text-[var(--accent)] mb-1">Conservative</h4>
                <p className="text-xs text-[var(--text-secondary)]">Only fixes obvious artifacts and markdown.</p>
              </label>
              <label className="border border-[var(--border-subtle)] bg-[var(--bg-elevated)] hover:border-[var(--border-strong)] rounded-lg p-4 cursor-pointer transition-colors">
                <input type="radio" name="sensitivity" value="balanced" className="sr-only" />
                <h4 className="font-medium text-[var(--text-primary)] mb-1">Balanced</h4>
                <p className="text-xs text-[var(--text-secondary)]">Artifacts plus moderate style improvements.</p>
              </label>
              <label className="border border-[var(--border-subtle)] bg-[var(--bg-elevated)] hover:border-[var(--border-strong)] rounded-lg p-4 cursor-pointer transition-colors">
                <input type="radio" name="sensitivity" value="aggressive" className="sr-only" />
                <h4 className="font-medium text-[var(--text-primary)] mb-1">Aggressive</h4>
                <p className="text-xs text-[var(--text-secondary)]">Broad rewrites and aggressive AI-style removal.</p>
              </label>
            </div>
          </div>

          <div className="pt-4 border-t border-[var(--border-subtle)] flex justify-between items-center">
            <div className="text-sm text-[var(--text-muted)]">
              Files are processed locally. No external APIs used.
            </div>
            <button 
              type="submit" 
              disabled={isProcessing}
              className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-6 py-2.5 rounded-md font-medium transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {isProcessing ? (
                <>
                  <div className="w-4 h-4 border-2 border-white border-t-transparent rounded-full animate-spin" />
                  Analyzing...
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
