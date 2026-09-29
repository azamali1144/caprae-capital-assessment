"use client";

import Link from "next/link";

import { Badge } from "@/components/ui/badge";
import { Skeleton } from "@/components/ui/skeleton";

import { useRecentImports } from "../hooks";
import type { ImportJob } from "../types";

const STATUS_VARIANT: Record<ImportJob["status"], "default" | "secondary" | "destructive" | "outline"> = {
  queued: "outline",
  running: "default",
  completed: "secondary",
  failed: "destructive",
};

function when(iso: string) {
  return new Date(iso).toLocaleString(undefined, { dateStyle: "medium", timeStyle: "short" });
}

export function RecentImports() {
  const { data, isLoading } = useRecentImports();

  if (isLoading) return <Skeleton className="h-32 w-full" />;
  if (!data?.length) {
    return <p className="text-sm text-muted-foreground">No imports yet - your history shows up here.</p>;
  }

  return (
    <ul className="divide-y rounded-lg border">
      {data.map((job) => (
        <li key={job.id} className="flex items-center gap-3 px-4 py-3 text-sm">
          <div className="min-w-0 flex-1">
            <p className="truncate font-medium">{job.filename ?? "Pasted domains"}</p>
            <p className="text-xs text-muted-foreground">
              {when(job.created_at)} · {job.total_rows} rows · {job.duplicates_removed} dupes removed
            </p>
          </div>
          <Badge variant={STATUS_VARIANT[job.status]}>{job.status}</Badge>
          {job.status === "completed" && (
            <Link href={`/leads?import=${job.id}`} className="text-primary hover:underline">
              View
            </Link>
          )}
        </li>
      ))}
    </ul>
  );
}
