"use client";

import { useMutation, useQueryClient } from "@tanstack/react-query";
import { Ban, CheckCheck, Download, PhoneCall, RefreshCw, Trash2, X } from "lucide-react";
import { toast } from "sonner";

import { Button } from "@/components/ui/button";

import { leadsApi } from "../api";
import { leadKeys, useLeadFilters } from "../hooks";
import type { BulkAction, Lead, Page, Stage } from "../types";

type Props = {
  ids: string[];
  onDone: () => void;
};

export function BulkActionsBar({ ids, onDone }: Props) {
  const qc = useQueryClient();
  const filters = useLeadFilters();

  const bulk = useMutation({
    mutationFn: (body: BulkAction) => leadsApi.bulk(body),
    // stage changes show up instantly, rolled back if the api says no
    onMutate: async (body) => {
      if (body.action !== "set_stage") return;
      await qc.cancelQueries({ queryKey: [...leadKeys.all, "list"] });
      const previous = qc.getQueriesData<Page<Lead>>({ queryKey: [...leadKeys.all, "list"] });
      qc.setQueriesData<Page<Lead>>({ queryKey: [...leadKeys.all, "list"] }, (old) =>
        old
          ? {
              ...old,
              items: old.items.map((l) => (ids.includes(l.id) ? { ...l, stage: body.value } : l)),
            }
          : old,
      );
      return { previous };
    },
    onError: (err, _body, ctx) => {
      ctx?.previous?.forEach(([key, data]) => qc.setQueryData(key, data));
      toast.error("Bulk action failed", { description: err.message });
    },
    onSuccess: (res, body) => {
      const label =
        body.action === "set_stage"
          ? `Moved ${res.affected} to ${body.value}`
          : body.action === "re_enrich"
            ? `Re-enriching ${res.affected} lead(s) in the background`
            : `Deleted ${res.affected} lead(s)`;
      toast.success(label);
      onDone();
    },
    onSettled: () => qc.invalidateQueries({ queryKey: leadKeys.all }),
  });

  const setStage = (value: Stage) => bulk.mutate({ ids, action: "set_stage", value });

  if (!ids.length) return null;

  return (
    <div className="fixed inset-x-0 bottom-4 z-40 flex justify-center px-4">
      <div className="flex flex-wrap items-center gap-1 rounded-xl border bg-background/95 p-1.5 shadow-lg backdrop-blur">
        <span className="px-2 text-sm font-medium tabular-nums">{ids.length} selected</span>
        <Button size="sm" variant="ghost" disabled={bulk.isPending} onClick={() => setStage("qualified")}>
          <CheckCheck className="text-indigo-500" /> Qualify
        </Button>
        <Button size="sm" variant="ghost" disabled={bulk.isPending} onClick={() => setStage("contacted")}>
          <PhoneCall className="text-emerald-500" /> Contacted
        </Button>
        <Button
          size="sm"
          variant="ghost"
          disabled={bulk.isPending}
          onClick={() => setStage("disqualified")}
        >
          <Ban className="text-rose-500" /> Disqualify
        </Button>
        <Button
          size="sm"
          variant="ghost"
          disabled={bulk.isPending}
          onClick={() => bulk.mutate({ ids, action: "re_enrich" })}
        >
          <RefreshCw /> Re-enrich
        </Button>
        <Button
          size="sm"
          variant="ghost"
          nativeButton={false}
          render={<a href={leadsApi.exportUrl(filters, ids)} download />}
        >
          <Download /> Export
        </Button>
        <Button
          size="sm"
          variant="ghost"
          className="text-destructive"
          disabled={bulk.isPending}
          onClick={() => {
            if (confirm(`Delete ${ids.length} lead(s) and their contacts? This can't be undone.`)) {
              bulk.mutate({ ids, action: "delete" });
            }
          }}
        >
          <Trash2 /> Delete
        </Button>
        <Button size="icon-sm" variant="ghost" aria-label="Clear selection" onClick={onDone}>
          <X />
        </Button>
      </div>
    </div>
  );
}
