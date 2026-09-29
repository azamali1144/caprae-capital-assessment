"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "sonner";

import { leadsApi } from "./api";
import { leadKeys } from "./hooks";
import type { LeadDetail, Stage } from "./types";

export function useUpdateLead(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: (body: { stage?: Stage; notes?: string | null }) => leadsApi.update(id, body),
    onSuccess: (lead) => {
      qc.setQueryData<LeadDetail>(leadKeys.detail(id), lead);
      qc.invalidateQueries({ queryKey: [...leadKeys.all, "list"] });
    },
    onError: (err) => toast.error("Couldn't save", { description: err.message }),
  });
}

export function useReEnrich(id: string) {
  const qc = useQueryClient();
  return useMutation({
    mutationFn: () => leadsApi.reEnrich(id),
    onSuccess: (lead) => {
      qc.setQueryData<LeadDetail>(leadKeys.detail(id), lead);
      qc.invalidateQueries({ queryKey: [...leadKeys.all, "list"] });
      toast.success("Re-enriched", { description: `Score is now ${lead.score ?? "—"}` });
    },
    onError: (err) => toast.error("Re-enrich failed", { description: err.message }),
  });
}
