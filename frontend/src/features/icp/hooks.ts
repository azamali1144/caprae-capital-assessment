"use client";

import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";

import { apiGet, apiPost, apiPut } from "@/lib/api-client";

import type { IcpProfile, IcpProfileInput } from "./types";

const KEY = ["icp-profiles"] as const;

export function useIcpProfiles() {
  return useQuery({ queryKey: KEY, queryFn: () => apiGet<IcpProfile[]>("/icp-profiles") });
}

export function useActiveProfile() {
  const { data } = useIcpProfiles();
  return data?.find((p) => p.is_active);
}

export function useSaveProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ id, input }: { id?: string; input: IcpProfileInput }) =>
      id
        ? apiPut<IcpProfile>(`/icp-profiles/${id}`, input)
        : apiPost<IcpProfile>("/icp-profiles", input),
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: KEY });
      qc.invalidateQueries({ queryKey: ["leads"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}

export function useActivateProfile() {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (id: string) =>
      apiPost<{ profile: IcpProfile; rescored: number }>(`/icp-profiles/${id}/activate`),
    onSuccess: () => {
      // every score just changed
      qc.invalidateQueries({ queryKey: KEY });
      qc.invalidateQueries({ queryKey: ["leads"] });
      qc.invalidateQueries({ queryKey: ["stats"] });
    },
  });
}
