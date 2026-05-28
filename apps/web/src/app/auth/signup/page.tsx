/* eslint-disable */
"use client";

import { useState } from "react";
import Link from "next/link";
import { useRouter } from "next/navigation";
import { AuthAPI } from "@/lib/api";
import { Lock, Mail, User, ArrowRight } from "lucide-react";

export default function SignupPage() {
  const router = useRouter();
  const [fullName, setFullName] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setError(null);

    // Simple validation
    if (!fullName || !email || !password) {
      setError("Please fill in all fields.");
      return;
    }

    if (password.length < 8) {
      setError("Password must be at least 8 characters long.");
      return;
    }

    setLoading(true);
    try {
      const res = await AuthAPI.signup({
        email,
        password,
        full_name: fullName,
      });
      localStorage.setItem("docppt_token", res.access_token);
      localStorage.setItem("docppt_user", JSON.stringify(res.user));
      
      // Dispatch storage event to notify other tabs/layout
      window.dispatchEvent(new Event("storage"));
      
      router.push("/dashboard");
    } catch (err: any) {
      setError(err.message || "Registration failed. Please try again.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="flex flex-col items-center justify-center min-h-[70vh] py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8 p-8 rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] backdrop-blur-md shadow-2xl relative overflow-hidden">
        {/* Glow effect */}
        <div className="absolute -top-24 -left-24 w-48 h-48 rounded-full bg-[var(--accent)] opacity-10 blur-3xl pointer-events-none" />
        <div className="absolute -bottom-24 -right-24 w-48 h-48 rounded-full bg-[var(--accent)] opacity-10 blur-3xl pointer-events-none" />

        <div className="text-center relative">
          <h2 className="mt-2 text-3xl font-extrabold text-[var(--text-primary)] tracking-tight">
            Create Account
          </h2>
          <p className="mt-2 text-sm text-[var(--text-secondary)]">
            Start analyzing documents and decks for free
          </p>
        </div>

        {error && (
          <div className="p-4 rounded-lg bg-red-500/10 border border-red-500/20 text-sm text-[var(--danger)] text-center animate-pulse">
            {error}
          </div>
        )}

        <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
          <div className="space-y-4 rounded-md shadow-sm">
            <div className="relative">
              <label htmlFor="full-name" className="sr-only">
                Full Name
              </label>
              <User className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-muted)]" />
              <input
                id="full-name"
                name="name"
                type="text"
                required
                value={fullName}
                onChange={(e) => setFullName(e.target.value)}
                className="appearance-none rounded-lg relative block w-full pl-11 pr-4 py-3 border border-[var(--border-subtle)] bg-[var(--bg-elevated)] placeholder-[var(--text-muted)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition-all sm:text-sm"
                placeholder="Full name"
              />
            </div>
            <div className="relative">
              <label htmlFor="email-address" className="sr-only">
                Email Address
              </label>
              <Mail className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-muted)]" />
              <input
                id="email-address"
                name="email"
                type="email"
                autoComplete="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="appearance-none rounded-lg relative block w-full pl-11 pr-4 py-3 border border-[var(--border-subtle)] bg-[var(--bg-elevated)] placeholder-[var(--text-muted)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition-all sm:text-sm"
                placeholder="Email address"
              />
            </div>
            <div className="relative">
              <label htmlFor="password" className="sr-only">
                Password
              </label>
              <Lock className="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-[var(--text-muted)]" />
              <input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="appearance-none rounded-lg relative block w-full pl-11 pr-4 py-3 border border-[var(--border-subtle)] bg-[var(--bg-elevated)] placeholder-[var(--text-muted)] text-[var(--text-primary)] focus:outline-none focus:ring-2 focus:ring-[var(--accent)] focus:border-transparent transition-all sm:text-sm"
                placeholder="Password (min. 8 characters)"
              />
            </div>
          </div>

          <div>
            <button
              type="submit"
              disabled={loading}
              className="group relative w-full flex justify-center py-3 px-4 border border-transparent text-sm font-semibold rounded-lg text-white bg-[var(--accent)] hover:bg-[var(--accent-hover)] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[var(--accent)] transition-all transform hover:-translate-y-0.5"
            >
              {loading ? (
                <div className="w-5 h-5 border-2 border-white/30 border-t-white rounded-full animate-spin" />
              ) : (
                <span className="flex items-center gap-2">
                  Create Account <ArrowRight className="w-4 h-4" />
                </span>
              )}
            </button>
          </div>
        </form>

        <div className="text-center mt-6 text-sm">
          <span className="text-[var(--text-secondary)]">Already have an account? </span>
          <Link
            href="/auth/login"
            className="font-medium text-[var(--accent)] hover:text-[var(--accent-hover)] transition-colors"
          >
            Sign In
          </Link>
        </div>
      </div>
    </div>
  );
}
