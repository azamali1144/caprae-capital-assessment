import { Skeleton } from "@/components/ui/skeleton";

export function TableSkeleton({ rows = 8, cols = 6 }: { rows?: number; cols?: number }) {
  return (
    <div className="divide-y rounded-lg border">
      {Array.from({ length: rows }).map((_, r) => (
        <div key={r} className="flex items-center gap-4 px-4 py-3">
          {Array.from({ length: cols }).map((_, c) => (
            <Skeleton
              key={c}
              className="h-4"
              // vary widths a bit so it doesn't look like a barcode
              style={{ width: c === 0 ? "22%" : `${8 + ((r + c) % 4) * 3}%` }}
            />
          ))}
        </div>
      ))}
    </div>
  );
}
