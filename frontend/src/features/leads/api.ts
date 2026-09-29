import { apiGet, apiPatch, apiPost, buildUrl } from "@/lib/api-client";

import type { BulkAction, Lead, LeadDetail, LeadFilters, Page, Stage } from "./types";

// drop empty bits so urls stay tidy (and cache keys stable)
export function toQuery(f: LeadFilters) {
  return {
    q: f.q,
    grade: f.grade?.length ? f.grade : undefined,
    min_score: f.min_score || undefined,
    industry: f.industry,
    country: f.country,
    stage: f.stage,
    email_status: f.email_status,
    import: f.import,
    sort: f.sort,
    order: f.order,
    page: f.page,
    page_size: f.page_size,
  };
}

export const leadsApi = {
  list: (f: LeadFilters) => apiGet<Page<Lead>>("/leads", toQuery(f)),
  get: (id: string) => apiGet<LeadDetail>(`/leads/${id}`),
  update: (id: string, body: { stage?: Stage; notes?: string | null }) =>
    apiPatch<LeadDetail>(`/leads/${id}`, body),
  bulk: (body: BulkAction) => apiPost<{ action: string; affected: number }>("/leads/bulk", body),
  reEnrich: (id: string) => apiPost<LeadDetail>(`/leads/${id}/enrich`, undefined, { force: true }),
  // export ignores paging - you get everything that matches the filters
  exportUrl: (f: LeadFilters, ids?: string[]) =>
    buildUrl("/exports/csv", { ...toQuery({ ...f, page: undefined, page_size: undefined }), ids }),
};
