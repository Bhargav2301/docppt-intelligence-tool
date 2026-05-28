import React from "react";

type Props = {
  label: "safe_replace" | "needs_shorter_option" | "manual_review";
};

export default function SafetyLabelBadge({ label }: Props) {
  if (label === "safe_replace") return null;

  if (label === "needs_shorter_option") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-semibold bg-yellow-500/10 text-yellow-600 border border-yellow-500/20">
        ⚠ Shorter needed
      </span>
    );
  }

  if (label === "manual_review") {
    return (
      <span className="inline-flex items-center gap-1 px-2 py-1 rounded-md text-xs font-semibold bg-red-500/10 text-red-500 border border-red-500/20">
        🔴 Manual review
      </span>
    );
  }

  return null;
}
