import Link from "next/link";
import { Presentation, ArrowRight } from "lucide-react";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] text-center px-4 animate-fade-in">
      <h1 className="text-4xl sm:text-5xl font-extrabold tracking-tight mb-6 bg-gradient-to-r from-[var(--text-primary)] via-[var(--accent)] to-[var(--text-primary)] bg-clip-text text-transparent">
        PowerPoint AI-Likeness Detector & Humanizer
      </h1>
      <p className="text-lg text-[var(--text-secondary)] max-w-2xl mb-12">
        Detect AI-like writing patterns in your presentations, review suggested rewrites, and compile a cleaned deck with 100% layout and slide fidelity.
      </p>

      <div className="flex justify-center w-full max-w-xl">
        <Link 
          href="/process/ppt"
          className="group flex flex-col items-start text-left p-8 rounded-2xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--accent)] hover:shadow-2xl hover:-translate-y-1 transition-all w-full relative overflow-hidden"
        >
          {/* Glow effect on hover */}
          <div className="absolute -top-24 -left-24 w-48 h-48 rounded-full bg-[var(--accent)] opacity-5 group-hover:opacity-10 blur-3xl pointer-events-none transition-all" />
          
          <div className="p-4 rounded-xl bg-orange-500/10 mb-6">
            <Presentation className="w-10 h-10 text-orange-500" />
          </div>
          <h2 className="text-2xl font-bold mb-3 flex items-center gap-2 text-[var(--text-primary)]">
            Humanize Presentation Decks
            <ArrowRight className="w-5 h-5 opacity-0 -ml-2 group-hover:opacity-100 group-hover:ml-0 transition-all text-[var(--accent)]" />
          </h2>
          <p className="text-[var(--text-secondary)] leading-relaxed">
            Scan PPTX slides for mechanical AI artifacts, generic business phrases, and low-burstiness phrasing. Edit, accept, and export cleaned slides safely.
          </p>
        </Link>
      </div>

      <div className="mt-16 text-sm text-[var(--text-muted)] flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-purple-500 animate-pulse" />
        Supports privacy-first Bring-Your-Own-Key Gemini model integration.
      </div>
    </div>
  );
}
