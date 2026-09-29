"use client";

import { CircleCheck, CircleHelp, CircleX, MailWarning, Trash2 } from "lucide-react";

import { Tooltip, TooltipContent, TooltipTrigger } from "@/components/ui/tooltip";
import type { EmailStatus } from "@/features/leads/types";
import { cn } from "@/lib/utils";

const META: Record<EmailStatus, { icon: typeof CircleCheck; label: string; className: string }> = {
  valid_mx: { icon: CircleCheck, label: "Domain accepts mail (MX found)", className: "text-emerald-600" },
  no_mx: { icon: CircleX, label: "Domain has no mail server", className: "text-rose-500" },
  invalid_syntax: { icon: MailWarning, label: "Not a valid email address", className: "text-rose-500" },
  disposable: { icon: Trash2, label: "Disposable inbox", className: "text-amber-500" },
  unknown: { icon: CircleHelp, label: "Couldn't verify yet", className: "text-muted-foreground" },
};

export function EmailStatusIcon({
  status,
  role,
  className,
}: {
  status: EmailStatus;
  role?: boolean;
  className?: string;
}) {
  const { icon: Icon, label, className: color } = META[status];
  return (
    <Tooltip>
      <TooltipTrigger render={<span className={cn("inline-flex", className)} />}>
        <Icon className={cn("size-4", color)} aria-label={label} />
      </TooltipTrigger>
      <TooltipContent>
        {label}
        {role ? " · generic inbox (info@, sales@…)" : ""}
      </TooltipContent>
    </Tooltip>
  );
}
