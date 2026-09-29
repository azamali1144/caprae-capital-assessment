"use client";

import { ArrowRight, Upload } from "lucide-react";
import Link from "next/link";

import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { ScoreBadge } from "@/components/shared/score-badge";
import { StatusChip } from "@/components/shared/status-chip";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Skeleton } from "@/components/ui/skeleton";
import { GradeChart } from "@/features/dashboard/components/grade-chart";
import { KpiCards } from "@/features/dashboard/components/kpi-cards";
import { useStats, useTopLeads } from "@/features/dashboard/hooks";

export default function DashboardPage() {
  const { data: stats, isLoading } = useStats();
  const { data: top } = useTopLeads(5);

  const empty = stats && stats.total_leads === 0;

  return (
    <div>
      <PageHeader
        title="Dashboard"
        description="How clean, reachable and on-target your lead lists are."
        actions={
          <Button nativeButton={false} render={<Link href="/imports" />}>
            <Upload /> Import leads
          </Button>
        }
      />

      {empty ? (
        <EmptyState
          icon={Upload}
          title="Import your first list"
          description="Drop in a SaaSquatch export (or just a list of domains). LeadLens dedupes it, checks every website and email, and ranks the lot - usually in under two minutes."
          action={<Button nativeButton={false} render={<Link href="/imports" />}>Get started</Button>}
        />
      ) : (
        <div className="space-y-6">
          <KpiCards stats={stats} loading={isLoading} />

          <div className="grid gap-6 lg:grid-cols-5">
            <Card className="lg:col-span-3">
              <CardHeader>
                <CardTitle className="text-base">Grade distribution</CardTitle>
              </CardHeader>
              <CardContent>
                {stats ? (
                  <GradeChart distribution={stats.grade_distribution} />
                ) : (
                  <Skeleton className="h-56 w-full" />
                )}
              </CardContent>
            </Card>

            <Card className="lg:col-span-2">
              <CardHeader className="flex flex-row items-center justify-between">
                <CardTitle className="text-base">Top 5 leads</CardTitle>
                <Link
                  href="/leads"
                  className="inline-flex items-center gap-1 text-sm text-primary hover:underline"
                >
                  All leads <ArrowRight className="size-3.5" />
                </Link>
              </CardHeader>
              <CardContent>
                {!top ? (
                  <Skeleton className="h-56 w-full" />
                ) : (
                  <ul className="divide-y">
                    {top.items.map((l) => (
                      <li key={l.id}>
                        <Link
                          href={`/leads?lead=${l.id}`}
                          className="flex items-center gap-3 py-2.5 hover:opacity-80"
                        >
                          <ScoreBadge score={l.score} grade={l.grade} />
                          <div className="min-w-0 flex-1">
                            <p className="truncate text-sm font-medium">{l.name}</p>
                            <p className="truncate text-xs text-muted-foreground">
                              {l.top_reasons[0] ?? l.domain}
                            </p>
                          </div>
                          <StatusChip stage={l.stage} />
                        </Link>
                      </li>
                    ))}
                  </ul>
                )}
              </CardContent>
            </Card>
          </div>
        </div>
      )}
    </div>
  );
}
