"use client";

import { CheckCircle2, Plus, Zap } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/shared/page-header";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Dialog,
  DialogClose,
  DialogContent,
  DialogDescription,
  DialogFooter,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";
import { Skeleton } from "@/components/ui/skeleton";
import { IcpForm, MODES } from "@/features/icp/components/icp-form";
import { useActivateProfile, useIcpProfiles, useSaveProfile } from "@/features/icp/hooks";
import type { IcpProfile } from "@/features/icp/types";
import { cn } from "@/lib/utils";

export default function IcpSettingsPage() {
  const { data: profiles, isLoading } = useIcpProfiles();
  const save = useSaveProfile();
  const activate = useActivateProfile();
  const [selectedId, setSelectedId] = useState<string | null>(null);
  const [creating, setCreating] = useState(false);
  const [confirming, setConfirming] = useState<IcpProfile | null>(null);

  const selected = creating
    ? undefined
    : (profiles?.find((p) => p.id === selectedId) ?? profiles?.find((p) => p.is_active) ?? profiles?.[0]);

  function doActivate(p: IcpProfile) {
    activate.mutate(p.id, {
      onSuccess: (res) =>
        toast.success(`"${p.name}" is now active`, {
          description: `Re-scored ${res.rescored} lead(s) with the ${MODES[p.mode].label.toLowerCase()} lens.`,
        }),
      onError: (e) => toast.error("Couldn't activate", { description: e.message }),
      onSettled: () => setConfirming(null),
    });
  }

  return (
    <div className="mx-auto max-w-5xl">
      <PageHeader
        title="ICP settings"
        description="Step 3 of 3 - define what a great lead looks like. Switching profiles re-scores everything."
        actions={
          <Button
            variant="outline"
            onClick={() => {
              setCreating(true);
              setSelectedId(null);
            }}
          >
            <Plus /> New profile
          </Button>
        }
      />

      <div className="grid gap-6 md:grid-cols-[16rem_1fr]">
        <div className="space-y-2">
          {isLoading && <Skeleton className="h-32 w-full" />}
          {profiles?.map((p) => {
            const { icon: Icon, label } = MODES[p.mode];
            const on = !creating && selected?.id === p.id;
            return (
              <div
                key={p.id}
                className={cn(
                  "rounded-lg border p-3 transition-colors",
                  on ? "border-primary bg-primary/5" : "hover:bg-muted/40",
                )}
              >
                <button
                  type="button"
                  className="w-full text-left"
                  onClick={() => {
                    setCreating(false);
                    setSelectedId(p.id);
                  }}
                >
                  <p className="flex items-center gap-2 text-sm font-medium">
                    <Icon className="size-4 text-muted-foreground" /> {p.name}
                  </p>
                  <p className="mt-0.5 text-xs text-muted-foreground">{label} lens</p>
                </button>
                <div className="mt-2">
                  {p.is_active ? (
                    <Badge variant="secondary">
                      <CheckCircle2 className="text-emerald-600" /> Active
                    </Badge>
                  ) : (
                    <Button size="xs" variant="outline" onClick={() => setConfirming(p)}>
                      <Zap /> Activate & re-score
                    </Button>
                  )}
                </div>
              </div>
            );
          })}
        </div>

        <Card>
          <CardHeader>
            <CardTitle className="text-base">
              {creating ? "New profile" : selected ? `Edit "${selected.name}"` : "Profile"}
            </CardTitle>
          </CardHeader>
          <CardContent>
            {isLoading ? (
              <Skeleton className="h-80 w-full" />
            ) : (
              <IcpForm
                key={creating ? "new" : selected?.id}
                profile={selected}
                saving={save.isPending}
                onSubmit={(input) =>
                  save.mutate(
                    { id: selected?.id, input },
                    {
                      onSuccess: (p) => {
                        toast.success(creating ? "Profile created" : "Saved", {
                          description: p.is_active ? "Scores updated with the new rules." : undefined,
                        });
                        setCreating(false);
                        setSelectedId(p.id);
                      },
                      onError: (e) => toast.error("Couldn't save", { description: e.message }),
                    },
                  )
                }
              />
            )}
          </CardContent>
        </Card>
      </div>

      <Dialog open={!!confirming} onOpenChange={(o) => !o && setConfirming(null)}>
        <DialogContent>
          <DialogHeader>
            <DialogTitle>Switch to &ldquo;{confirming?.name}&rdquo;?</DialogTitle>
            <DialogDescription>
              {confirming && MODES[confirming.mode].blurb} Every lead gets re-scored - it only takes a
              moment and nothing is re-crawled.
            </DialogDescription>
          </DialogHeader>
          <DialogFooter>
            <DialogClose render={<Button variant="outline" />}>Cancel</DialogClose>
            <Button disabled={activate.isPending} onClick={() => confirming && doActivate(confirming)}>
              {activate.isPending ? "Re-scoring…" : "Activate & re-score"}
            </Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
}
