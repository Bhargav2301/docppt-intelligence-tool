import Link from "next/link";
import { FileText, Presentation, ArrowRight } from "lucide-react";

export default function Home() {
  return (
    <div className="flex flex-col items-center justify-center min-h-[80vh] text-center px-4">
      <h1 className="text-4xl sm:text-5xl font-bold tracking-tight mb-6">
        Professional Document Intelligence
      </h1>
      <p className="text-lg text-[var(--text-secondary)] max-w-2xl mb-12">
        Analyze Google Docs to extract product requirements, or humanize PowerPoint 
        presentations with local, privacy-first NLP models.
      </p>

      <div className="grid grid-cols-1 md:grid-cols-2 gap-6 w-full max-w-4xl">
        <Link 
          href="/process/doc"
          className="group flex flex-col items-start text-left p-8 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--accent)] hover:shadow-lg transition-all"
        >
          <div className="p-3 rounded-lg bg-blue-500/10 mb-6">
            <FileText className="w-8 h-8 text-blue-500" />
          </div>
          <h2 className="text-2xl font-semibold mb-3 flex items-center gap-2">
            Analyze Document
            <ArrowRight className="w-5 h-5 opacity-0 -ml-2 group-hover:opacity-100 group-hover:ml-0 transition-all text-[var(--accent)]" />
          </h2>
          <p className="text-[var(--text-secondary)]">
            Extract structured summaries, product descriptions, and prioritized implementation requirements from Google Docs or Word files.
          </p>
        </Link>

        <Link 
          href="/process/ppt"
          className="group flex flex-col items-start text-left p-8 rounded-xl border border-[var(--border-subtle)] bg-[var(--bg-surface)] hover:border-[var(--accent)] hover:shadow-lg transition-all"
        >
          <div className="p-3 rounded-lg bg-orange-500/10 mb-6">
            <Presentation className="w-8 h-8 text-orange-500" />
          </div>
          <h2 className="text-2xl font-semibold mb-3 flex items-center gap-2">
            Humanize PPT
            <ArrowRight className="w-5 h-5 opacity-0 -ml-2 group-hover:opacity-100 group-hover:ml-0 transition-all text-[var(--accent)]" />
          </h2>
          <p className="text-[var(--text-secondary)]">
            Detect mechanical AI artifacts, review suggested rewrites, and surgically compile a cleaned presentation without breaking layouts.
          </p>
        </Link>
      </div>

      <div className="mt-16 text-sm text-[var(--text-muted)] flex items-center gap-2">
        <div className="w-2 h-2 rounded-full bg-[var(--success)] animate-pulse" />
        Local models enabled. No paid API required.
      </div>
    </div>
  );
}
