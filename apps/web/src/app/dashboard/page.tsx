"use client";

import { useEffect, useState } from "react";
import Link from "next/link";
import { Plus, History, Clock, FileText, Presentation, Activity, RefreshCw, Eye, Trash2 } from "lucide-react";
import { SessionAPI, RecentSessionItem } from "@/lib/api";

export default function Dashboard() {
  const [sessions, setSessions] = useState<RecentSessionItem[]>([]);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    fetchSessions();
  }, []);

  const fetchSessions = async () => {
    try {
      setIsLoading(true);
      const data = await SessionAPI.getRecent();
      setSessions(data);
    } catch (e) {
      console.error(e);
    } finally {
      setIsLoading(false);
    }
  };

  const getStatusBadge = (status: string) => {
    switch (status) {
      case "completed":
        return <span className="px-2 py-1 rounded-md text-xs font-medium bg-[var(--success)]/10 text-[var(--success)] border border-[var(--success)]/20">Completed</span>;
      case "failed_final":
        return <span className="px-2 py-1 rounded-md text-xs font-medium bg-[var(--danger)]/10 text-[var(--danger)] border border-[var(--danger)]/20">Failed</span>;
      case "created":
      case "validating":
      case "extracting":
      case "analyzing":
        return <span className="px-2 py-1 rounded-md text-xs font-medium bg-[var(--warning)]/10 text-[var(--warning)] border border-[var(--warning)]/20 capitalize">{status}</span>;
      default:
        return <span className="px-2 py-1 rounded-md text-xs font-medium bg-[var(--border-subtle)] text-[var(--text-secondary)] border border-[var(--border-strong)] capitalize">{status}</span>;
    }
  };

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
        <div className="flex items-center justify-between border-b border-[var(--border-subtle)] px-6 py-4 bg-[var(--bg-elevated)]/50">
          <div className="flex items-center gap-2">
            <History className="w-5 h-5 text-[var(--text-secondary)]" />
            <h2 className="font-semibold">Recent Sessions</h2>
          </div>
          <button onClick={fetchSessions} className="text-[var(--text-secondary)] hover:text-[var(--text-primary)]" title="Refresh">
            <RefreshCw className={`w-4 h-4 ${isLoading ? "animate-spin text-[var(--accent)]" : ""}`} />
          </button>
        </div>
        
        <div className="p-0">
          {isLoading && sessions.length === 0 ? (
            <div className="flex justify-center py-12">
              <div className="w-6 h-6 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
            </div>
          ) : sessions.length === 0 ? (
            <div className="text-center py-12">
              <Clock className="w-12 h-12 text-[var(--text-muted)] mx-auto mb-4 opacity-50" />
              <p className="text-[var(--text-secondary)]">No processing sessions yet.</p>
              <p className="text-sm text-[var(--text-muted)] mt-1">Start by analyzing a document or PPT above.</p>
            </div>
          ) : (
            <div className="divide-y divide-[var(--border-subtle)]">
              {sessions.map(session => (
                <div key={session.id} className="p-4 hover:bg-[var(--bg-elevated)] transition-colors flex items-center justify-between">
                  <div className="flex items-center gap-4">
                    <div className={`p-2 rounded-lg ${session.session_type === 'doc' ? 'bg-blue-500/10 text-blue-500' : 'bg-orange-500/10 text-orange-500'}`}>
                      {session.session_type === 'doc' ? <FileText className="w-5 h-5" /> : <Presentation className="w-5 h-5" />}
                    </div>
                    <div>
                      <h4 className="font-medium text-[var(--text-primary)] truncate max-w-[300px]">
                        {session.input_label}
                      </h4>
                      <div className="flex items-center gap-2 mt-1 text-xs text-[var(--text-muted)]">
                        <span className="uppercase font-semibold tracking-wider">{session.session_type}</span>
                        <span>•</span>
                        <span>{new Date(session.created_at).toLocaleString()}</span>
                        {session.metrics?.word_count && (
                          <>
                            <span>•</span>
                            <span>{session.metrics.word_count} words</span>
                          </>
                        )}
                      </div>
                      {session.status === 'failed_final' && session.error_message && (
                        <p className="text-xs text-red-500 mt-1.5 italic font-medium bg-red-500/5 px-2.5 py-1.5 rounded-lg border border-red-500/10 max-w-[500px] break-words">
                          Error: {session.error_message}
                        </p>
                      )}
                    </div>
                  </div>
                  <div className="flex items-center gap-2">
                    {getStatusBadge(session.status)}
                    
                    {session.status === 'completed' && (
                      <Link 
                        href={session.session_type === 'doc' ? `/session/${session.id}` : `/review/ppt/${session.id}`}
                        className="p-2 text-[var(--text-secondary)] hover:text-[var(--accent)] hover:bg-[var(--accent)]/10 rounded-md transition-colors"
                        title="View Results"
                      >
                        <Eye className="w-4 h-4" />
                      </Link>
                    )}

                    <button
                      onClick={async () => {
                        if (confirm("Are you sure you want to delete this session?")) {
                          try {
                            await SessionAPI.delete(session.id);
                            setSessions(sessions.filter(s => s.id !== session.id));
                          } catch (e) {
                            console.error(e);
                            alert("Failed to delete session");
                          }
                        }
                      }}
                      className="p-2 text-[var(--text-secondary)] hover:text-[var(--danger)] hover:bg-[var(--danger)]/10 rounded-md transition-colors"
                      title="Delete Session"
                    >
                      <Trash2 className="w-4 h-4" />
                    </button>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
