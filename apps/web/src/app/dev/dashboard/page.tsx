"use client";

import { useState, useEffect } from "react";
import { useRouter } from "next/navigation";
import { TelemetryAPI, TelemetryEvent, UserProfile } from "@/lib/api";
import { ShieldAlert, RefreshCw, ChevronDown, ChevronUp, Search, Calendar, BarChart2, Filter } from "lucide-react";

export default function DevDashboardPage() {
  const router = useRouter();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [events, setEvents] = useState<TelemetryEvent[]>([]);
  const [total, setTotal] = useState(0);
  const [page, setPage] = useState(1);
  const [limit] = useState(20);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [expandedRows, setExpandedRows] = useState<Record<string, boolean>>({});
  
  // Filtering states
  const [routeFilter, setRouteFilter] = useState("");
  const [typeFilter, setTypeFilter] = useState("");

  const checkDevAccess = () => {
    const userStr = localStorage.getItem("docppt_user");
    if (!userStr) {
      router.push("/auth/login");
      return;
    }
    try {
      const parsedUser = JSON.parse(userStr) as UserProfile;
      setUser(parsedUser);
      if (parsedUser.role !== "developer") {
        setLoading(false);
      } else {
        fetchEvents();
      }
    } catch (e) {
      router.push("/auth/login");
    }
  };

  const fetchEvents = async () => {
    setLoading(true);
    setError(null);
    try {
      const res = await TelemetryAPI.getEvents(page, limit);
      setEvents(res.events);
      setTotal(res.total);
    } catch (err: any) {
      setError(err.message || "Failed to fetch telemetry logs.");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    checkDevAccess();
  }, [page]);

  const toggleRow = (id: string) => {
    setExpandedRows((prev) => ({
      ...prev,
      [id]: !prev[id],
    }));
  };

  const handleRefresh = () => {
    fetchEvents();
  };

  // Compute stats for charts
  const routeCounts = events.reduce((acc, ev) => {
    const r = ev.route || "Unknown";
    acc[r] = (acc[r] || 0) + 1;
    return acc;
  }, {} as Record<string, number>);

  const sortedRouteCounts = Object.entries(routeCounts).sort((a, b) => b[1] - a[1]);

  if (loading && events.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh]">
        <div className="w-10 h-10 border-4 border-[var(--accent)]/30 border-t-[var(--accent)] rounded-full animate-spin" />
        <span className="mt-4 text-sm text-[var(--text-secondary)]">Loading Developer Panel...</span>
      </div>
    );
  }

  if (user && user.role !== "developer") {
    return (
      <div className="flex flex-col items-center justify-center min-h-[60vh] text-center max-w-md mx-auto p-6 rounded-2xl border border-[var(--danger)]/20 bg-[var(--bg-surface)]">
        <ShieldAlert className="w-16 h-16 text-[var(--danger)] animate-pulse" />
        <h1 className="mt-4 text-2xl font-bold text-[var(--text-primary)]">Access Denied</h1>
        <p className="mt-2 text-sm text-[var(--text-secondary)] leading-relaxed">
          Your account does not possess developer privileges. Telemetry logs and system health reports are restricted.
        </p>
        <button
          onClick={() => router.push("/dashboard")}
          className="mt-6 px-4 py-2 rounded-lg bg-[var(--accent)] hover:bg-[var(--accent-hover)] text-white text-xs font-semibold transition-all"
        >
          Return to Dashboard
        </button>
      </div>
    );
  }

  return (
    <div className="space-y-8 animate-fade-in">
      <div className="flex flex-col md:flex-row md:items-center md:justify-between gap-4 border-b border-[var(--border-subtle)] pb-6">
        <div>
          <h1 className="text-3xl font-extrabold text-[var(--text-primary)] tracking-tight">
            Developer Observability Dashboard
          </h1>
          <p className="mt-1 text-sm text-[var(--text-secondary)]">
            Live telemetry, crash diagnostics, and PII-redacted exception tracebacks.
          </p>
        </div>
        <button
          onClick={handleRefresh}
          className="flex items-center gap-2 px-4 py-2 text-xs font-semibold rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-elevated)] transition-all"
        >
          <RefreshCw className="w-4 h-4" /> Refresh Logs
        </button>
      </div>

      {/* Metric Cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
        <div className="p-5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <span className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">Total Crashes Captured</span>
          <h3 className="text-3xl font-bold text-[var(--text-primary)] mt-1">{total}</h3>
        </div>
        <div className="p-5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <span className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">Telemetry Consent Rate</span>
          <h3 className="text-3xl font-bold text-[var(--success)] mt-1">100%</h3>
        </div>
        <div className="p-5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <span className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">Active Microservices</span>
          <h3 className="text-3xl font-bold text-blue-400 mt-1">1 / 1</h3>
        </div>
        <div className="p-5 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
          <span className="text-xs font-semibold text-[var(--text-muted)] uppercase tracking-wider">Exception Clean Rate</span>
          <h3 className="text-3xl font-bold text-orange-400 mt-1">100%</h3>
        </div>
      </div>

      {/* SVG Chart */}
      <div className="p-6 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)]">
        <h3 className="text-lg font-bold text-[var(--text-primary)] mb-4 flex items-center gap-2">
          <BarChart2 className="w-5 h-5 text-[var(--accent)]" /> Exceptions by Endpoint
        </h3>
        
        {sortedRouteCounts.length === 0 ? (
          <div className="text-center py-8 text-sm text-[var(--text-muted)]">
            No crash records found to chart.
          </div>
        ) : (
          <div className="space-y-4">
            {sortedRouteCounts.map(([route, count]) => {
              const percentage = Math.round((count / events.length) * 100);
              return (
                <div key={route} className="space-y-1">
                  <div className="flex justify-between text-xs font-medium">
                    <span className="text-[var(--text-secondary)] font-mono">{route}</span>
                    <span className="text-[var(--text-primary)]">{count} crash(es) ({percentage}%)</span>
                  </div>
                  <div className="w-full h-3 rounded-full bg-[var(--bg-elevated)] overflow-hidden">
                    <div
                      className="h-full bg-[var(--accent)] rounded-full transition-all duration-500"
                      style={{ width: `${percentage}%` }}
                    />
                  </div>
                </div>
              );
            })}
          </div>
        )}
      </div>

      {/* Logs Table */}
      <div className="border border-[var(--border-subtle)] rounded-xl bg-[var(--bg-surface)] overflow-hidden">
        <div className="p-4 border-b border-[var(--border-subtle)] bg-[var(--bg-elevated)]/30 flex flex-wrap items-center justify-between gap-4">
          <h3 className="text-lg font-bold text-[var(--text-primary)]">
            Telemetry Exception Events
          </h3>
          <span className="text-xs text-[var(--text-muted)]">
            Showing {events.length} of {total} events
          </span>
        </div>

        {events.length === 0 ? (
          <div className="p-12 text-center text-sm text-[var(--text-muted)]">
            No telemetry logs available. Beautiful day!
          </div>
        ) : (
          <div className="divide-y divide-[var(--border-subtle)]">
            {events.map((ev) => {
              const isExpanded = !!expandedRows[ev.id];
              return (
                <div key={ev.id} className="transition-colors hover:bg-[var(--bg-elevated)]/10">
                  <div
                    onClick={() => toggleRow(ev.id)}
                    className="flex items-center justify-between p-4 cursor-pointer gap-4"
                  >
                    <div className="flex-1 grid grid-cols-1 md:grid-cols-4 gap-4 items-center">
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-0.5 rounded text-[10px] font-bold bg-red-500/10 text-[var(--danger)] border border-red-500/20 uppercase">
                          {ev.error_type}
                        </span>
                        <span className="text-xs text-[var(--text-muted)] font-mono">
                          {new Date(ev.timestamp).toLocaleTimeString()}
                        </span>
                      </div>
                      <div className="text-sm font-semibold text-[var(--text-primary)] md:col-span-2 truncate">
                        {ev.message}
                      </div>
                      <div className="text-xs text-[var(--text-muted)] font-mono truncate">
                        {ev.route}
                      </div>
                    </div>
                    <div>
                      {isExpanded ? (
                        <ChevronUp className="w-5 h-5 text-[var(--text-muted)]" />
                      ) : (
                        <ChevronDown className="w-5 h-5 text-[var(--text-muted)]" />
                      )}
                    </div>
                  </div>

                  {isExpanded && (
                    <div className="p-4 bg-[var(--bg-elevated)]/40 border-t border-[var(--border-subtle)] text-xs space-y-4 animate-fade-in">
                      <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 border-b border-[var(--border-subtle)] pb-4 text-[var(--text-secondary)]">
                        <div>
                          <strong>Event ID:</strong> <span className="font-mono">{ev.id}</span>
                        </div>
                        <div>
                          <strong>Linked User ID:</strong> <span className="font-mono">{ev.user_id || "Anonymous"}</span>
                        </div>
                        <div>
                          <strong>Timestamp:</strong> <span>{new Date(ev.timestamp).toLocaleString()}</span>
                        </div>
                      </div>
                      
                      <div className="space-y-1">
                        <strong className="text-[var(--text-secondary)]">Sanitized Message:</strong>
                        <div className="p-3 rounded-lg bg-[var(--bg-elevated)] border border-[var(--border-subtle)] font-mono text-[var(--text-primary)]">
                          {ev.message}
                        </div>
                      </div>

                      {ev.stack_summary && (
                        <div className="space-y-1">
                          <strong className="text-[var(--text-secondary)]">PII-Scrubbed Traceback Trace:</strong>
                          <pre className="p-4 rounded-lg bg-[var(--bg-base)] border border-[var(--border-subtle)] text-[var(--text-secondary)] font-mono overflow-x-auto leading-relaxed max-h-[300px]">
                            {ev.stack_summary}
                          </pre>
                        </div>
                      )}
                    </div>
                  )}
                </div>
              );
            })}
          </div>
        )}

        {/* Pagination controls */}
        {total > limit && (
          <div className="p-4 border-t border-[var(--border-subtle)] flex items-center justify-between">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] disabled:opacity-30 disabled:pointer-events-none transition-all"
            >
              Previous
            </button>
            <span className="text-xs text-[var(--text-muted)] font-medium">
              Page {page} of {Math.ceil(total / limit)}
            </span>
            <button
              onClick={() => setPage((p) => p + 1)}
              disabled={page * limit >= total}
              className="px-3 py-1.5 rounded-lg border border-[var(--border-subtle)] text-xs font-semibold text-[var(--text-secondary)] hover:text-[var(--text-primary)] disabled:opacity-30 disabled:pointer-events-none transition-all"
            >
              Next
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
