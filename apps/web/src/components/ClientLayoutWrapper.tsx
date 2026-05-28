/* eslint-disable */
"use client";

import { useState, useEffect } from "react";
import Link from "next/link";
import { useRouter, usePathname } from "next/navigation";
import { AuthAPI, UserProfile, TelemetryAPI } from "@/lib/api";
import CrashConsentModal from "@/components/CrashConsentModal";
import { Shield, LogOut, Settings, BarChart2, User as UserIcon } from "lucide-react";

export default function ClientLayoutWrapper({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const pathname = usePathname();
  const [user, setUser] = useState<UserProfile | null>(null);
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [backendWaking, setBackendWaking] = useState(false);
  const [isCheckingAuth, setIsCheckingAuth] = useState(true);
  const [pendingCrash, setPendingCrash] = useState<{
    message: string;
    errorType: string;
    stack: string | null;
  } | null>(null);

  // Sync auth state on load and when localStorage changes
  const checkAuth = async () => {
    const token = localStorage.getItem("docppt_token");
    if (!token) {
      setUser(null);
      setIsCheckingAuth(false);
      // Redirect to login if accessing dashboard or other restricted routes, but not auth routes or landing page
      if (pathname !== "/" && !pathname.startsWith("/auth/")) {
        router.push("/auth/login");
      }
      return;
    }

    let retries = 2;
    let delay = 1000;

    while (true) {
      try {
        const profile = await AuthAPI.getMe();
        setUser(profile);
        localStorage.setItem("docppt_user", JSON.stringify(profile));
        setBackendWaking(false);
        setIsCheckingAuth(false);
        break;
      } catch (err: any) {
        // True auth failures (e.g. 401 or 403)
        const isAuthFailure = err && (err.status === 401 || err.status === 403);

        if (isAuthFailure) {
          localStorage.removeItem("docppt_token");
          localStorage.removeItem("docppt_user");
          setUser(null);
          setBackendWaking(false);
          setIsCheckingAuth(false);
          if (pathname !== "/" && !pathname.startsWith("/auth/")) {
            router.push("/auth/login");
          }
          break;
        }

        // Network error, timeout, or server error (5xx)
        if (retries > 0) {
          setBackendWaking(true);
          retries--;
          await new Promise((resolve) => setTimeout(resolve, delay));
          delay *= 2;
        } else {
          // Out of retries, preserve token to avoid kicking user out, but stop trying
          setBackendWaking(false);
          setIsCheckingAuth(false);
          break;
        }
      }
    }
  };

  useEffect(() => {
    setIsCheckingAuth(true);
    checkAuth();

    // Listen to localStorage changes across tabs/components
    const handleStorageChange = () => {
      checkAuth();
    };

    window.addEventListener("storage", handleStorageChange);
    return () => {
      window.removeEventListener("storage", handleStorageChange);
    };
  }, [pathname]);

  // Global error telemetry capture
  useEffect(() => {
    const triggerTelemetry = (message: string, errorType: string, stack: string | null) => {
      const consent = localStorage.getItem("docppt_crash_consent");

      if (consent === "granted") {
        TelemetryAPI.recordCrash({
          route: window.location.pathname,
          error_type: errorType,
          message,
          stack_summary: stack,
          consent_flag: true,
        }).catch(console.error);
      } else if (consent === null) {
        setPendingCrash({ message, errorType, stack });
        setIsModalOpen(true);
      }
    };

    const handleError = (event: ErrorEvent) => {
      const error = event.error;
      const message = error?.message || event.message || "Unknown error";
      const stack = error?.stack || null;
      const errorType = error?.name || "Error";
      
      triggerTelemetry(message, errorType, stack);
    };

    const handleRejection = (event: PromiseRejectionEvent) => {
      const reason = event.reason;
      const message = reason?.message || (typeof reason === "string" ? reason : "Unhandled rejection");
      const stack = reason?.stack || null;
      const errorType = reason?.name || "UnhandledRejection";

      triggerTelemetry(message, errorType, stack);
    };

    window.addEventListener("error", handleError);
    window.addEventListener("unhandledrejection", handleRejection);
    return () => {
      window.removeEventListener("error", handleError);
      window.removeEventListener("unhandledrejection", handleRejection);
    };
  }, []);

  const handleModalClose = (consentGranted: boolean) => {
    setIsModalOpen(false);
    if (consentGranted && pendingCrash) {
      TelemetryAPI.recordCrash({
        route: window.location.pathname,
        error_type: pendingCrash.errorType,
        message: pendingCrash.message,
        stack_summary: pendingCrash.stack,
        consent_flag: true,
      }).catch(console.error);
    }
    setPendingCrash(null);
  };

  const handleLogout = async () => {
    try {
      await AuthAPI.logout();
    } catch (e) {
      // Ignored if invalid already
    }
    localStorage.removeItem("docppt_token");
    localStorage.removeItem("docppt_user");
    setUser(null);
    window.dispatchEvent(new Event("storage"));
    router.push("/auth/login");
  };

  return (
    <>
      {/* Dynamic Header Nav */}
      <header className="sticky top-0 z-40 w-full border-b border-[var(--border-subtle)] bg-[var(--bg-base)]/80 backdrop-blur-md">
        <div className="mx-auto max-w-7xl px-4 sm:px-6 lg:px-8">
          <div className="flex h-16 items-center justify-between">
            <div className="flex items-center gap-8">
              <Link href="/" className="font-extrabold text-[var(--text-primary)] text-xl tracking-wider hover:text-[var(--accent)] transition-colors">
                DocPPT
              </Link>
              {user && (
                <nav className="hidden md:flex gap-6">
                  <Link href="/dashboard" className={`text-sm font-medium transition-colors ${pathname === "/dashboard" ? "text-[var(--accent)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}>
                    Dashboard
                  </Link>
                  <Link href="/process/ppt" className={`text-sm font-medium transition-colors ${pathname === "/process/ppt" ? "text-[var(--accent)]" : "text-[var(--text-secondary)] hover:text-[var(--text-primary)]"}`}>
                    Humanize PPT
                  </Link>
                </nav>
              )}
            </div>
            
            <div className="flex items-center gap-4">
              {user ? (
                <>
                  {user.role === "developer" && (
                    <Link
                      href="/dev/dashboard"
                      className="flex items-center gap-1 text-xs font-semibold px-3 py-1.5 rounded-lg bg-blue-500/10 border border-blue-500/20 text-blue-400 hover:bg-blue-500/20 hover:border-blue-400/50 transition-all"
                    >
                      <BarChart2 className="w-4 h-4" /> Dev Panel
                    </Link>
                  )}
                  <Link
                    href="/settings"
                    className="p-2 rounded-lg border border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:bg-[var(--bg-elevated)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] transition-all"
                    title="Settings"
                  >
                    <Settings className="w-4 h-4" />
                  </Link>
                  <div className="flex items-center gap-2 pl-2 border-l border-[var(--border-subtle)]">
                    <div className="w-8 h-8 rounded-full bg-[var(--accent)]/15 border border-[var(--accent)]/30 flex items-center justify-center text-xs font-bold text-[var(--accent)]" title={user.full_name}>
                      <UserIcon className="w-4 h-4" />
                    </div>
                    <span className="hidden sm:inline text-xs font-medium text-[var(--text-secondary)] max-w-[120px] truncate">
                      {user.full_name}
                    </span>
                    <button
                      onClick={handleLogout}
                      className="p-2 rounded-lg text-red-400 hover:bg-red-500/10 transition-all ml-1"
                      title="Log Out"
                    >
                      <LogOut className="w-4 h-4" />
                    </button>
                  </div>
                </>
              ) : (
                <div className="flex items-center gap-3">
                  <Link
                    href="/auth/login"
                    className="text-xs font-semibold px-4 py-2 rounded-lg border border-[var(--border-subtle)] text-[var(--text-secondary)] hover:text-[var(--text-primary)] hover:bg-[var(--bg-surface)] transition-all"
                  >
                    Sign In
                  </Link>
                  <Link
                    href="/auth/signup"
                    className="text-xs font-semibold px-4 py-2 rounded-lg text-white bg-[var(--accent)] hover:bg-[var(--accent-hover)] transition-all transform hover:-translate-y-0.5"
                  >
                    Sign Up
                  </Link>
                </div>
              )}
            </div>
          </div>
        </div>
      </header>

      {backendWaking && (
        <div className="bg-amber-500/10 border-b border-amber-500/20 text-amber-400 py-2.5 px-4 text-center text-xs font-semibold flex items-center justify-center gap-2 animate-pulse">
          <span className="w-2 h-2 rounded-full bg-amber-400 animate-ping" />
          Backend is waking up (cold start). Retrying connection...
        </div>
      )}

      {/* Main Page Children */}
      <main className="flex-1 w-full mx-auto max-w-7xl px-4 sm:px-6 lg:px-8 py-8">
        {isCheckingAuth && pathname !== "/" && !pathname.startsWith("/auth/") ? (
          <div className="flex flex-col items-center justify-center min-h-[50vh] space-y-4">
            <div className="w-8 h-8 border-2 border-[var(--accent)] border-t-transparent rounded-full animate-spin" />
            <p className="text-sm text-[var(--text-secondary)] font-medium">
              {backendWaking ? "Backend is waking up, please wait..." : "Checking session..."}
            </p>
          </div>
        ) : (
          children
        )}
      </main>

      {/* global consent modal */}
      <CrashConsentModal isOpen={isModalOpen} onClose={handleModalClose} />
    </>
  );
}
