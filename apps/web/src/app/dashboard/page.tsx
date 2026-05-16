"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, History, Clock, FileText, Presentation, Activity } from "lucide-react";
import { apiFetch } from "@/lib/api";

type Session = {
  id: string;
  source_filename: string;
  session_type: "doc" | "ppt";
  status: string;
  created_at: string;
};

export default function Dashboard() {
  const [sessions, setSessions] = useState<Session[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    // In a real implementation we would fetch from /api/sessions
    // For now we'll stub it out so the UI renders
    setSessions([]);
    setIsLoading(false);
  }, []);

  return (
    <div className="max-w-5xl mx-auto space-y-8">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold tracking-tight">Dashboard</h1>
          <p className="text-[var(--text-secondary)] mt-1">Manage your document processing sessions.</p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-2 px-3 py-1.5 bg-[var(--bg-elevated)] border border-[var(--border-subtle)] rounded-md text-sm">
            <Activity className="w-4 h-4 text-[var(--success)]" />
            <span className="text-[var(--text-secondary)]">API: Connected</span>
          </div>
        </div>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        <Link 
          href="/process/doc"
          className="flex items-center gap-4 p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--accent)] hover:bg-[var(--bg-elevated)] transition-all group"
        >
          <div className="p-3 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] group-hover:border-[var(--accent)] transition-colors">
            <Plus className="w-5 h-5 text-[var(--accent)]" />
          </div>
          <div>
            <h3 className="font-semibold text-lg text-[var(--text-primary)]">New Doc Analysis</h3>
            <p className="text-sm text-[var(--text-secondary)]">Extract specs from a Google Doc</p>
          </div>
        </Link>

        <Link 
          href="/process/ppt"
          className="flex items-center gap-4 p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--accent)] hover:bg-[var(--bg-elevated)] transition-all group"
        >
          <div className="p-3 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] group-hover:border-[var(--accent)] transition-colors">
            <Plus className="w-5 h-5 text-[var(--accent)]" />
          </div>
          <div>
            <h3 className="font-semibold text-lg text-[var(--text-primary)]">New PPT Review</h3>
            <p className="text-sm text-[var(--text-secondary)]">Clean and humanize a presentation</p>
          </div>
        </Link>
      </div>

      <div className="rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] overflow-hidden">
        <div className="flex items-center gap-2 border-b border-[var(--border-subtle)] px-6 py-4 bg-[var(--bg-elevated)]/50">
          <History className="w-5 h-5 text-[var(--text-secondary)]" />
          <h2 className="font-semibold">Recent Sessions</h2>
        </div>
        
        <div className="p-6">
          {isLoading ? (
            <div className="flex justify-center py-8">
              <div className="w-6 h-6 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-12">
              <Clock className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-4 opacity-50" />
              <p className="text-[var(--text-secondary)]">No processing sessions yet.</p>
              <p className="text-sm text-[var(--text-muted)] mt-1">Start by analyzing a document or PPT above.</p>
            </div>
          ) : (
            <div className="space-y-2">
              {/* List rendering would go here */}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
