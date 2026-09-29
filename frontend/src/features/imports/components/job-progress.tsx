"use client";

import { CheckCircle2, Loader2, XCircle } from "lucide-react";
import Link from "next/link";
import { useEffect, useRef } from "react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Progress } from "@/components/ui/progress";
import { cn } from "@/lib/utils";

import { useImportJob } from "../hooks";
import { isActive, jobTarget } from "../types";

function Stat({ label, value, tone }: { label: string; value: number; tone?: string }) {
  return (
    <div>
      <p className={cn("text-xl font-semibold tabular-nums", tone)}>{value.toLocaleString()}</p>
      <p className="text-xs text-muted-foreground">{label}</p>
    </div>
  );
}

export function JobProgress({ jobId, warnings = [] }: { jobId: string; warnings?: string[] }) {
  const { data: job } = useImportJob(jobId);
  const announced = useRef(false);

  const running = isActive(job);
  const target = job ? jobTarget(job) : 0;
  const done = job ? job.processed + job.failed : 0;
  const pct = target ? Math.round((done / target) * 100) : running ? 0 : 100;

  useEffect(() => {
    if (!job || running || announced.current) return;
    announced.current = true;
    if (job.status === "completed") {
      toast.success(`Enriched ${job.processed} companies`, {
        description: job.duplicates_removed
          ? `${job.duplicates_removed} duplicates removed along the way.`
          : undefined,
      });
    } else {
      toast.error("Import failed", { description: job.error ?? undefined });
    }
  }, [job, running]);

  if (!job) return null;

  return (
    <Card>
      <CardHeader className="flex flex-row items-center justify-between gap-2">
        <CardTitle className="flex items-center gap-2 text-base">
          {running ? (
            <Loader2 className="size-4 animate-spin text-primary" />
          ) : job.status === "completed" ? (
            <CheckCircle2 className="size-4 text-emerald-600" />
          ) : (
            <XCircle className="size-4 text-destructive" />
          )}
          {running ? "Enriching your leads…" : job.status === "completed" ? "All done" : "Import failed"}
        </CardTitle>
        <span className="text-sm text-muted-foreground">{job.filename ?? "Pasted domains"}</span>
      </CardHeader>
      <CardContent className="space-y-4">
        <div className="space-y-1.5">
          <Progress value={pct} />
          <p className="text-xs text-muted-foreground">
            {done.toLocaleString()} of {target.toLocaleString()} companies · crawling public
            sites, checking MX records, scoring
          </p>
        </div>

        <div className="grid grid-cols-2 gap-4 sm:grid-cols-4">
          <Stat label="Rows in file" value={job.total_rows} />
          <Stat label="Duplicates removed" value={job.duplicates_removed} tone="text-amber-600" />
          <Stat label="Enriched" value={job.processed} tone="text-emerald-600" />
          <Stat label="Failed" value={job.failed} tone={job.failed ? "text-destructive" : undefined} />
        </div>

        {warnings.length > 0 && (
          <ul className="list-inside list-disc text-xs text-muted-foreground">
            {warnings.map((w) => (
              <li key={w}>{w}</li>
            ))}
          </ul>
        )}

        {!running && job.status === "completed" && (
          <Button nativeButton={false} render={<Link href={`/leads?import=${job.id}`} />}>View leads</Button>
        )}
      </CardContent>
    </Card>
  );
}
