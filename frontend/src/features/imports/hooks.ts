"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { importsApi } from "./api";
import { isActive } from "./types";

export const importKeys = {
  all: ["imports"] as const,
  recent: () => [...importKeys.all, "recent"] as const,
  job: (id: string) => [...importKeys.all, "job", id] as const,
};

export function useCreateImport() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (input: { file: File } | { domains: string[] }) =>
      "file" in input ? importsApi.uploadCsv(input.file) : importsApi.importDomains(input.domains),
    onSuccess: (res) => {
      qc.setQueryData(importKeys.job(res.job_id), res.job);
      qc.invalidateQueries({ queryKey: importKeys.recent() });
    },
  });
}

export function useImportJob(id: string | null) {
  return useQuery({
    queryKey: importKeys.job(id ?? ""),
    queryFn: () => importsApi.get(id!),
    enabled: !!id,
    // poll while the crawler is working, stop once it's done
    refetchInterval: (q) => (isActive(q.state.data) ? 2000 : false),
  });
}

export function useRecentImports() {
  return useQuery({
    queryKey: importKeys.recent(),
    queryFn: () => importsApi.recent(),
    refetchInterval: (q) => (q.state.data?.some(isActive) ? 4000 : false),
  });
}
