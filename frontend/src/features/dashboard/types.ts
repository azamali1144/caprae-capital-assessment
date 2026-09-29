// mirrors backend/app/api/v1/stats.py

export interface Stats {
  total_leads: number;
  duplicates_removed_total: number;
  enriched: number;
  leads_with_email: number;
  valid_email_rate: number;
  avg_score: number | null;
  grade_distribution: Record<"A" | "B" | "C" | "D", number>;
  by_stage: Record<"new" | "qualified" | "contacted" | "disqualified", number>;
}
