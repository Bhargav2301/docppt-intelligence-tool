/* eslint-disable */
"use client";

import { useState } from "react";
import { AlertCircle, Check, X, ShieldAlert } from "lucide-react";

type CrashConsentModalProps = {
  isOpen: boolean;
  onClose: (consent: boolean) => void;
};

export default function CrashConsentModal({ isOpen, onClose }: CrashConsentModalProps) {
  if (!isOpen) return null;

  const handleConsent = (granted: boolean) => {
    localStorage.setItem("docppt_crash_consent", granted ? "granted" : "denied");
    
    // Also sync to UserSettings if a user settings endpoint is available
    onClose(granted);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 bg-black/60 backdrop-blur-sm animate-fade-in">
      <div className="relative max-w-md w-full p-6 rounded-2xl border border-orange-500/30 bg-[var(--bg-surface)] shadow-[0_0_50px_rgba(245,166,35,0.15)] overflow-hidden">
        {/* Glow accent */}
        <div className="absolute -top-12 -left-12 w-24 h-24 rounded-full bg-orange-500/10 blur-2xl pointer-events-none" />

        <div className="flex items-start gap-4">
          <div className="p-3 rounded-lg bg-orange-500/10 text-orange-400">
            <ShieldAlert className="w-6 h-6 animate-bounce" />
          </div>
          <div className="flex-1 space-y-2">
            <h3 className="text-xl font-bold text-[var(--text-primary)]">
              Crash Telemetry Request
            </h3>
            <p className="text-sm text-[var(--text-secondary)] leading-relaxed">
              DocPPT encountered an unexpected error. To help developers fix issues and improve the app, would you allow sharing anonymous crash reports?
            </p>
          </div>
        </div>

        <div className="p-3 my-4 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] text-xs text-[var(--text-muted)] leading-relaxed">
          <strong className="text-[var(--text-secondary)]">Strict Privacy Policy:</strong> Crash reports contain only route names, generic error types, and sanitized tracebacks. They <span className="text-orange-400 font-semibold">never</span> transmit uploaded documents, pasted texts, or presentation contents.
        </div>

        <div className="flex items-center justify-end gap-3 mt-6">
          <button
            type="button"
            onClick={() => handleConsent(false)}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-all"
          >
            <X className="w-4 h-4" /> No, Keep Private
          </button>
          <button
            type="button"
            onClick={() => handleConsent(true)}
            className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg text-white bg-[var(--accent)] hover:bg-[var(--accent-hover)] transition-all transform hover:-translate-y-0.5"
          >
            <Check className="w-4 h-4" /> Yes, Share Report
          </button>
        </div>
      </div>
    </div>
  );
}
