import React from "react";

type Props = {
  score: number;
  band: "low" | "moderate" | "high";
  size?: "sm" | "md";
};

export default function AiLikenessBadge({ score, band, size = "md" }: Props) {
  const colorClasses = {
    high: "bg-red-500/10 text-red-500 border-red-500/20",
    moderate: "bg-yellow-500/10 text-yellow-600 border-yellow-500/20",
    low: "bg-teal-500/10 text-teal-600 border-teal-500/20",
  };

  const sizeClasses = {
    sm: "px-1.5 py-0.5 text-[10px]",
    md: "px-2.5 py-1 text-xs",
  };

  return (
    <span
      className={`inline-flex items-center font-bold uppercase tracking-wider border rounded-full transition-all ${colorClasses[band]} ${sizeClasses[size]}`}
    >
      {score}% {band}
    </span>
  );
}
