"use client";

import { useQuery } from "@tanstack/react-query";

import { leadsApi } from "@/features/leads/api";
import { apiGet } from "@/lib/api-client";

import type { Stats } from "./types";

export function useStats() {
  return useQuery({
    queryKey: ["stats"],
    queryFn: () => apiGet<Stats>("/stats"),
    refetchInterval: 30_000,
  });
}

export function useTopLeads(n = 5) {
  return useQuery({
    queryKey: ["leads", "top", n],
    queryFn: () => leadsApi.list({ sort: "score", order: "desc", page: 1, page_size: n }),
  });
}
