"use client";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { Grade } from "@/features/leads/types";
import { cn } from "@/lib/utils";

export const GRADE_STYLES: Record<Grade, string> = {
  A: "bg-grade-a/15 text-emerald-700 ring-grade-a/40 dark:text-emerald-300",
  B: "bg-grade-b/15 text-sky-700 ring-grade-b/40 dark:text-sky-300",
  C: "bg-grade-c/15 text-amber-700 ring-grade-c/40 dark:text-amber-300",
  D: "bg-grade-d/15 text-rose-700 ring-grade-d/40 dark:text-rose-300",
};

export const GRADE_LABEL: Record<Grade, string> = {
  A: "Top prospect",
  B: "Strong fit",
  C: "Maybe later",
  D: "Low priority",
};

type Props = {
  score: number | null;
  grade: Grade | null;
  reasons?: string[];
  size?: "sm" | "lg";
  className?: string;
};

export function ScoreBadge({ score, grade, reasons, size = "sm", className }: Props) {
  if (score === null || !grade) {
    return (
      <span className={cn("text-xs text-muted-foreground", className)} title="Not scored yet">
        —
      </span>
    );
  }

  const badge = (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full font-semibold tabular-nums ring-1 ring-inset",
        size === "lg" ? "px-3 py-1 text-base" : "px-2 py-0.5 text-xs",
        GRADE_STYLES[grade],
        className,
      )}
    >
      {score}
      <span className="opacity-70">·</span>
      {grade}
    </span>
  );

  if (!reasons?.length) return badge;

  return (
    <Tooltip>
      <TooltipTrigger render={<span className="cursor-help" />}>{badge}</TooltipTrigger>
      <TooltipContent side="right" className="block max-w-64">
        <p className="mb-1 font-medium">{GRADE_LABEL[grade]}</p>
        <ul className="space-y-0.5">
          {reasons.map((r) => (
            <li key={r}>+ {r}</li>
          ))}
        </ul>
      </TooltipContent>
    </Tooltip>
  );
}
