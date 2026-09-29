// mirrors backend/app/schemas/import_job.py

export type JobStatus = "queued" | "running" | "completed" | "failed";

export interface ImportJob {
  id: string;
  source: "csv" | "saasquatch_csv" | "domain_list";
  filename: string | null;
  status: JobStatus;
  total_rows: number;
  duplicates_removed: number;
  processed: number;
  failed: number;
  error: string | null;
  started_at: string | null;
  finished_at: string | null;
  created_at: string;
}

export interface ImportCreated {
  job_id: string;
  job: ImportJob;
  unmapped_columns: string[];
  warnings: string[];
}

export const isActive = (job?: ImportJob) => job?.status === "queued" || job?.status === "running";

// companies that actually get enriched = rows minus the dupes we dropped
export const jobTarget = (job: ImportJob) => Math.max(job.total_rows - job.duplicates_removed, 0);
