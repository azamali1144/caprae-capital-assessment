import { CopyMinus, Gauge, MailCheck, Users } from "lucide-react";

import { StatCard } from "@/components/shared/stat-card";

import type { Stats } from "../types";

export function KpiCards({ stats, loading }: { stats?: Stats; loading?: boolean }) {
  const pct = (n: number) => `${Math.round(n * 100)}%`;

  return (
    <div className="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
      <StatCard
        label="Total leads"
        icon={Users}
        loading={loading}
        value={stats?.total_leads.toLocaleString()}
        hint={stats ? `${stats.enriched.toLocaleString()} enriched from their websites` : undefined}
      />
      <StatCard
        label="Duplicates removed"
        icon={CopyMinus}
        loading={loading}
        value={stats?.duplicates_removed_total.toLocaleString()}
        hint="Credits and outreach you didn't waste"
      />
      <StatCard
        label="Verified email rate"
        icon={MailCheck}
        loading={loading}
        value={stats ? pct(stats.valid_email_rate) : undefined}
        hint="Leads with at least one MX-verified email"
      />
      <StatCard
        label="Average score"
        icon={Gauge}
        loading={loading}
        value={stats?.avg_score ?? "—"}
        hint="Against your active ICP"
      />
    </div>
  );
}
