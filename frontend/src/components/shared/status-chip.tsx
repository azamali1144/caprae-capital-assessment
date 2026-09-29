import type { Stage } from "@/features/leads/types";
import { cn } from "@/lib/utils";

const STAGE_STYLES: Record<Stage, { label: string; dot: string; chip: string }> = {
  new: { label: "New", dot: "bg-slate-400", chip: "text-slate-700 dark:text-slate-300" },
  qualified: {
    label: "Qualified",
    dot: "bg-indigo-500",
    chip: "text-indigo-700 dark:text-indigo-300",
  },
  contacted: {
    label: "Contacted",
    dot: "bg-emerald-500",
    chip: "text-emerald-700 dark:text-emerald-300",
  },
  disqualified: {
    label: "Disqualified",
    dot: "bg-rose-400",
    chip: "text-muted-foreground line-through decoration-rose-400/60",
  },
};

export const stageLabel = (stage: Stage) => STAGE_STYLES[stage].label;

export function StatusChip({ stage, className }: { stage: Stage; className?: string }) {
  const s = STAGE_STYLES[stage];
  return (
    <span
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-2 py-0.5 text-xs font-medium",
        s.chip,
        className,
      )}
    >
      <span className={cn("size-1.5 rounded-full", s.dot)} />
      {s.label}
    </span>
  );
}
