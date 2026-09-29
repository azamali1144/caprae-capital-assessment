import { cn } from "@/lib/utils";

import type { ScoreItem } from "../types";

// "Why this score" - every point has a reason, nothing hidden
export function ScoreBreakdown({ items, score }: { items: ScoreItem[]; score: number | null }) {
  if (!items.length) {
    return <p className="text-sm text-muted-foreground">No scoring signals yet - try re-enriching.</p>;
  }

  const maxAbs = Math.max(...items.map((i) => Math.abs(i.points)), 1);
  const raw = items.reduce((sum, i) => sum + i.points, 0);

  return (
    <div className="space-y-2">
      <ul className="space-y-1.5">
        {items.map((item) => {
          const positive = item.points > 0;
          return (
            <li key={item.rule} className="grid grid-cols-[3rem_1fr] items-center gap-3">
              <span
                className={cn(
                  "text-right text-sm font-semibold tabular-nums",
                  positive ? "text-emerald-600 dark:text-emerald-400" : "text-rose-600 dark:text-rose-400",
                )}
              >
                {positive ? "+" : ""}
                {item.points}
              </span>
              <div className="min-w-0">
                <p className="text-sm">{item.reason}</p>
                <div className="mt-1 h-1 rounded-full bg-muted">
                  <div
                    className={cn("h-1 rounded-full", positive ? "bg-emerald-500" : "bg-rose-500")}
                    style={{ width: `${(Math.abs(item.points) / maxAbs) * 100}%` }}
                  />
                </div>
              </div>
            </li>
          );
        })}
      </ul>
      {score !== null && raw !== score && (
        <p className="text-xs text-muted-foreground">
          Raw total {raw}, clamped to {score} (scores stay between 0 and 100).
        </p>
      )}
    </div>
  );
}
