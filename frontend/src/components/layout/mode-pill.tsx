"use client";

import { useQuery } from "@tanstack/react-query";
import { Briefcase, Target } from "lucide-react";
import Link from "next/link";

import type { IcpProfile } from "@/features/icp/types";
import { apiGet } from "@/lib/api-client";
import { cn } from "@/lib/utils";

// shows which scoring lens is on - clicking it jumps to the icp settings
export function ModePill() {
  const { data } = useQuery({
    queryKey: ["icp-profiles"],
    queryFn: () => apiGet<IcpProfile[]>("/icp-profiles"),
  });

  const active = data?.find((p) => p.is_active);
  if (!active) return null;

  const acquisition = active.mode === "acquisition";
  const Icon = acquisition ? Briefcase : Target;

  return (
    <Link
      href="/settings/icp"
      title={active.name}
      className={cn(
        "inline-flex items-center gap-1.5 rounded-full border px-3 py-1 text-xs font-medium transition-colors",
        acquisition
          ? "border-violet-300 bg-violet-50 text-violet-700 hover:bg-violet-100 dark:border-violet-800 dark:bg-violet-950 dark:text-violet-300"
          : "border-indigo-300 bg-indigo-50 text-indigo-700 hover:bg-indigo-100 dark:border-indigo-800 dark:bg-indigo-950 dark:text-indigo-300",
      )}
    >
      <Icon className="size-3.5" />
      {acquisition ? "Acquisition fit" : "Sales"} mode
    </Link>
  );
}
