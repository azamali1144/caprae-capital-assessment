"use client";

import { keepPreviousData, useQuery } from "@tanstack/react-query";
import {
  parseAsArrayOf,
  parseAsInteger,
  parseAsString,
  parseAsStringLiteral,
  useQueryStates,
} from "nuqs";

import { leadsApi } from "./api";
import { GRADES, STAGES, type LeadFilters } from "./types";

export const leadKeys = {
  all: ["leads"] as const,
  list: (f: LeadFilters) => [...leadKeys.all, "list", f] as const,
  detail: (id: string) => [...leadKeys.all, "detail", id] as const,
};

const SORTS = ["score", "name", "created_at", "last_enriched_at", "employee_count", "founded_year"] as const;
const EMAIL_STATUSES = ["valid_mx", "no_mx", "invalid_syntax", "disposable", "unknown"] as const;

// every filter lives in the url -> shareable views, back button just works
export const leadSearchParams = {
  q: parseAsString.withDefault(""),
  grade: parseAsArrayOf(parseAsStringLiteral(GRADES)).withDefault([]),
  min_score: parseAsInteger.withDefault(0),
  industry: parseAsString.withDefault(""),
  country: parseAsString.withDefault(""),
  stage: parseAsStringLiteral(STAGES),
  email_status: parseAsStringLiteral(EMAIL_STATUSES),
  import: parseAsString,
  sort: parseAsStringLiteral(SORTS).withDefault("score"),
  order: parseAsStringLiteral(["asc", "desc"] as const).withDefault("desc"),
  page: parseAsInteger.withDefault(1),
  page_size: parseAsInteger.withDefault(25),
  lead: parseAsString, // open drawer
};

export function useLeadSearchParams() {
  return useQueryStates(leadSearchParams, { history: "replace" });
}

export function useLeadFilters(): LeadFilters {
  const [p] = useLeadSearchParams();
  return {
    q: p.q || undefined,
    grade: p.grade,
    min_score: p.min_score || undefined,
    industry: p.industry || undefined,
    country: p.country || undefined,
    stage: p.stage ?? undefined,
    email_status: p.email_status ?? undefined,
    import: p.import ?? undefined,
    sort: p.sort,
    order: p.order,
    page: p.page,
    page_size: p.page_size,
  };
}

export function useLeads(filters: LeadFilters) {
  return useQuery({
    queryKey: leadKeys.list(filters),
    queryFn: () => leadsApi.list(filters),
    placeholderData: keepPreviousData, // no flicker when paging/sorting
  });
}

export function useLead(id: string | null) {
  return useQuery({
    queryKey: leadKeys.detail(id ?? ""),
    queryFn: () => leadsApi.get(id!),
    enabled: !!id,
  });
}
