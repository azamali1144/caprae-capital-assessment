import type { LucideIcon } from "lucide-react";

import { Card, CardContent } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { cn } from "@/lib/utils";

type Props = {
  label: string;
  value: React.ReactNode;
  hint?: string;
  icon?: LucideIcon;
  loading?: boolean;
  className?: string;
};

export function StatCard({ label, value, hint, icon: Icon, loading, className }: Props) {
  return (
    <Card className={cn("gap-0 py-4", className)}>
      <CardContent className="px-4">
        <div className="flex items-center justify-between text-sm text-muted-foreground">
          {label}
          {Icon && <Icon className="size-4" />}
        </div>
        {loading ? (
          <Skeleton className="mt-2 h-8 w-20" />
        ) : (
          <div className="mt-1 text-2xl font-semibold tabular-nums tracking-tight">{value}</div>
        )}
        {hint && <p className="mt-1 text-xs text-muted-foreground">{hint}</p>}
      </CardContent>
    </Card>
  );
}
