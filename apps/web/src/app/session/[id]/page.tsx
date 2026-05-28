"use client";

import { useEffect, useState, use } from "react";
import { useRouter } from "next/navigation";
import { Loader2, ArrowLeft } from "lucide-react";
import Link from "next/link";
import { SessionAPI } from "@/lib/api";

export default function SessionDetail({
  params,
}: {
  params: Promise<{ id: string }>;
}) {
  const { id } = use(params);
  const router = useRouter();
  const [error, setError] = useState("");

  useEffect(() => {
    SessionAPI.getDetail(id)
      .then((res) => {
        if (res.session.session_type === "ppt") {
          router.replace(`/review/ppt/${id}`);
        } else {
          setError("Unsupported session type.");
        }
      })
      .catch((e) => setError(e.message || "Failed to load session."));
  }, [id, router]);

  if (error) {
    return (
      <div className="max-w-4xl mx-auto mt-16 text-center space-y-4 text-[var(--text-primary)]">
        <h2 className="text-xl font-semibold">Session Error</h2>
        <p className="text-[var(--text-secondary)]">{error}</p>
        <Link
          href="/dashboard"
          className="inline-flex items-center gap-2 text-[var(--accent)] hover:underline mt-4"
        >
          <ArrowLeft className="w-4 h-4" /> Back to Dashboard
        </Link>
      </div>
    );
  }

  return (
    <div className="flex items-center justify-center min-h-[60vh]">
      <Loader2 className="w-8 h-8 text-[var(--accent)] animate-spin" />
    </div>
  );
}
