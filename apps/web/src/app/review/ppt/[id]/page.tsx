"use client";

import { useState, use } from "react";
import { Check, X, Edit2, AlertTriangle, Presentation, Download } from "lucide-react";

export default function PPTReview({ params }: { params: Promise<{ id: string }> }) {
  const { id } = use(params);
  
  // Dummy state for scaffolding
  const [activeSlide, setActiveSlide] = useState(1);

  return (
    <div className="max-w-7xl mx-auto h-[calc(100vh-8rem)] flex flex-col">
      {/* Header */}
      <div className="flex items-center justify-between mb-6 flex-shrink-0">
        <div>
          <h1 className="text-2xl font-bold tracking-tight">Review PPT Changes</h1>
          <p className="text-[var(--text-secondary)] text-sm mt-1">Session ID: {id}</p>
        </div>
        <button className="flex items-center gap-2 bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white px-5 py-2 rounded-md font-medium transition-colors">
          <Download className="w-4 h-4" />
          Export Clean PPT
        </button>
      </div>

      {/* Main Review Area */}
      <div className="flex-1 grid grid-cols-1 md:grid-cols-12 gap-6 min-h-0">
        
        {/* Left Panel: Slide List */}
        <div className="md:col-span-3 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl overflow-y-auto">
          <div className="p-4 border-b border-[var(--border-subtle)] sticky top-0 bg-[var(--bg-surface)]">
            <h2 className="font-semibold text-[var(--text-primary)] flex items-center gap-2">
              <Presentation className="w-4 h-4" />
              Slides (5)
            </h2>
          </div>
          <div className="p-2 space-y-1">
            {[1, 2, 3, 4, 5].map((slide) => (
              <button
                key={slide}
                onClick={() => setActiveSlide(slide)}
                className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  activeSlide === slide 
                    ? "bg-[var(--accent)]/10 text-[var(--accent)]" 
                    : "text-[var(--text-secondary)] hover:bg-[var(--bg-elevated)]"
                }`}
              >
                Slide {slide}
                {slide === 2 && <span className="float-right w-2 h-2 rounded-full bg-[var(--warning)] mt-1.5" />}
              </button>
            ))}
          </div>
        </div>

        {/* Center/Right Panel: Diff View */}
        <div className="md:col-span-9 bg-[var(--bg-surface)] border border-[var(--border-subtle)] rounded-xl flex flex-col min-h-0">
          <div className="p-6 border-b border-[var(--border-subtle)] flex-shrink-0">
            <h2 className="text-xl font-bold">Slide {activeSlide}</h2>
          </div>
          
          <div className="flex-1 overflow-y-auto p-6 space-y-8">
            {/* Example Card */}
            <div className="border border-[var(--border-subtle)] rounded-xl p-6 bg-[var(--bg-elevated)]/30">
              <div className="flex items-start justify-between mb-4">
                <span className="inline-flex items-center gap-1.5 px-2.5 py-1 rounded-md text-xs font-semibold bg-[var(--warning)]/10 text-[var(--warning)] border border-[var(--warning)]/20">
                  <AlertTriangle className="w-3.5 h-3.5" />
                  Citation Artifact
                </span>
                <div className="flex items-center gap-2">
                  <button className="p-1.5 text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] rounded-md transition-colors" title="Edit">
                    <Edit2 className="w-4 h-4" />
                  </button>
                  <button className="p-1.5 text-[var(--danger)] hover:bg-[var(--danger)]/10 rounded-md transition-colors" title="Reject">
                    <X className="w-4 h-4" />
                  </button>
                  <button className="p-1.5 text-[var(--success)] hover:bg-[var(--success)]/10 rounded-md transition-colors" title="Accept">
                    <Check className="w-4 h-4" />
                  </button>
                </div>
              </div>
              
              <div className="grid grid-cols-2 gap-6">
                <div>
                  <h4 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">Original</h4>
                  <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
                    This is a sample sentence with a citation [1]. It breaks the flow.
                  </p>
                </div>
                <div>
                  <h4 className="text-xs font-bold text-[var(--text-muted)] uppercase tracking-wider mb-2">Suggested Rewrite</h4>
                  <p className="text-sm text-[var(--text-primary)] leading-relaxed">
                    This is a sample sentence with a citation. It breaks the flow.
                  </p>
                </div>
              </div>
            </div>
            
          </div>
        </div>
        
      </div>
    </div>
  );
}
