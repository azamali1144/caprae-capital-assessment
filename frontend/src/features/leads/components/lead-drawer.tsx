"use client";

import {
  Check,
  Copy,
  Crown,
  ExternalLink,
  Globe,
  Lock,
  RefreshCw,
  Users,
} from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { EmailStatusIcon } from "@/components/shared/email-status-icon";
import { GRADE_LABEL, ScoreBadge } from "@/components/shared/score-badge";
import { stageLabel } from "@/components/shared/status-chip";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Separator } from "@/components/ui/separator";
import { Sheet, SheetContent, SheetDescription, SheetHeader, SheetTitle } from "@/components/ui/sheet";
import { Skeleton } from "@/components/ui/skeleton";
import { Textarea } from "@/components/ui/textarea";

import { useLead } from "../hooks";
import { useReEnrich, useUpdateLead } from "../mutations";
import { STAGES, type LeadDetail, type Stage } from "../types";
import { ScoreBreakdown } from "./score-breakdown";

function CopyButton({ value }: { value: string }) {
  const [done, setDone] = useState(false);
  return (
    <Button
      variant="ghost"
      size="icon-xs"
      aria-label={`Copy ${value}`}
      onClick={async () => {
        await navigator.clipboard.writeText(value);
        setDone(true);
        setTimeout(() => setDone(false), 1200);
      }}
    >
      {done ? <Check className="text-emerald-600" /> : <Copy />}
    </Button>
  );
}

function Section({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <section className="space-y-2">
      <h3 className="text-xs font-semibold tracking-wide text-muted-foreground uppercase">{title}</h3>
      {children}
    </section>
  );
}

function Fact({ label, value }: { label: string; value: React.ReactNode }) {
  return (
    <div>
      <dt className="text-xs text-muted-foreground">{label}</dt>
      <dd className="text-sm">{value ?? "—"}</dd>
    </div>
  );
}

function Signal({ on, label }: { on?: boolean; label: string }) {
  return (
    <Badge variant={on ? "secondary" : "outline"} className={on ? "" : "text-muted-foreground"}>
      {on ? <Check /> : null}
      {label}
    </Badge>
  );
}

function Body({ lead }: { lead: LeadDetail }) {
  const update = useUpdateLead(lead.id);
  const reEnrich = useReEnrich(lead.id);
  const years = lead.founded_year ? new Date().getFullYear() - lead.founded_year : null;

  return (
    <div className="space-y-6 px-4 pb-8">
      <div className="flex flex-wrap items-center gap-3">
        <ScoreBadge score={lead.score} grade={lead.grade} size="lg" />
        {lead.grade && <span className="text-sm text-muted-foreground">{GRADE_LABEL[lead.grade]}</span>}
        <Button
          variant="outline"
          size="sm"
          className="ml-auto"
          disabled={reEnrich.isPending || !lead.domain}
          onClick={() => reEnrich.mutate()}
        >
          <RefreshCw className={reEnrich.isPending ? "animate-spin" : ""} />
          {reEnrich.isPending ? "Crawling…" : "Re-enrich"}
        </Button>
      </div>

      <Section title="Why this score">
        <ScoreBreakdown items={lead.score_breakdown} score={lead.score} />
      </Section>

      <Separator />

      <Section title="Contacts">
        {lead.contacts.length === 0 ? (
          <p className="text-sm text-muted-foreground">No contacts found on the site.</p>
        ) : (
          <ul className="divide-y rounded-lg border">
            {lead.contacts.map((c) => (
              <li key={c.id} className="space-y-1 px-3 py-2.5">
                <div className="flex items-center gap-1.5">
                  <p className="text-sm font-medium">{c.full_name ?? "Unnamed contact"}</p>
                  {c.is_decision_maker && (
                    <Crown className="size-3.5 text-amber-500" aria-label="Decision maker" />
                  )}
                  {c.title && <span className="text-xs text-muted-foreground">· {c.title}</span>}
                </div>
                {c.email && (
                  <div className="flex items-center gap-1.5 text-sm">
                    <EmailStatusIcon status={c.email_status} role={c.email_type === "role"} />
                    <span className="truncate">{c.email}</span>
                    <CopyButton value={c.email} />
                  </div>
                )}
                {c.phone_e164 && (
                  <div className="flex items-center gap-1.5 text-sm text-muted-foreground">
                    <span className="tabular-nums">{c.phone_e164}</span>
                    {!c.phone_valid && <span className="text-xs">(unverified)</span>}
                    <CopyButton value={c.phone_e164} />
                  </div>
                )}
              </li>
            ))}
          </ul>
        )}
      </Section>

      <Section title="Company">
        {lead.description && <p className="text-sm text-muted-foreground">{lead.description}</p>}
        <dl className="grid grid-cols-2 gap-3">
          <Fact label="Industry" value={lead.industry} />
          <Fact
            label="Location"
            value={[lead.city, lead.state, lead.country].filter(Boolean).join(", ") || null}
          />
          <Fact label="Employees" value={lead.employee_count?.toLocaleString()} />
          <Fact
            label="Founded"
            value={lead.founded_year ? `${lead.founded_year} (${years} yrs)` : null}
          />
          <Fact label="Site last updated" value={lead.copyright_year ? `© ${lead.copyright_year}` : null} />
          <Fact label="Website" value={lead.website_status ?? "not checked"} />
        </dl>
        {lead.tech_stack.length > 0 && (
          <div className="flex flex-wrap gap-1.5 pt-1">
            {lead.tech_stack.map((t) => (
              <Badge key={t} variant="outline">
                {t}
              </Badge>
            ))}
          </div>
        )}
        {Object.keys(lead.socials).length > 0 && (
          <div className="flex flex-wrap gap-3 pt-1 text-sm">
            {Object.entries(lead.socials).map(([net, url]) => (
              <a
                key={net}
                href={url}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 text-primary capitalize hover:underline"
              >
                {net} <ExternalLink className="size-3" />
              </a>
            ))}
          </div>
        )}
      </Section>

      <Section title="Signals">
        <div className="flex flex-wrap gap-1.5">
          <Signal on={lead.signals.has_ssl} label="SSL" />
          <Signal on={lead.signals.hiring} label="Hiring" />
          <Signal on={lead.signals.family_owned} label="Family / owner-run" />
          <Signal on={lead.signals.modern_stack} label="Modern stack" />
        </div>
      </Section>

      <Separator />

      <Section title="Workflow">
        <Select
          value={lead.stage}
          onValueChange={(v) => update.mutate({ stage: v as Stage })}
        >
          <SelectTrigger className="w-44">
            <SelectValue>{(v: string) => stageLabel(v as Stage)}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            {STAGES.map((s) => (
              <SelectItem key={s} value={s}>
                {stageLabel(s)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>
        <Textarea
          key={lead.id}
          defaultValue={lead.notes ?? ""}
          placeholder="Notes - saved when you click away"
          className="min-h-24"
          onBlur={(e) => {
            const notes = e.target.value.trim() || null;
            if (notes !== (lead.notes ?? null)) {
              update.mutate({ notes }, { onSuccess: () => toast.success("Notes saved") });
            }
          }}
        />
      </Section>
    </div>
  );
}

export function LeadDrawer({ id, onClose }: { id: string | null; onClose: () => void }) {
  const { data: lead, isLoading } = useLead(id);

  return (
    <Sheet open={!!id} onOpenChange={(open) => !open && onClose()}>
      <SheetContent className="w-full overflow-y-auto sm:max-w-lg">
        <SheetHeader>
          <SheetTitle className="flex items-center gap-2 pr-6">
            {lead?.name ?? (isLoading ? <Skeleton className="h-5 w-40" /> : "Lead")}
          </SheetTitle>
          <SheetDescription className="flex items-center gap-2">
            {lead?.domain ? (
              <a
                href={lead.website_url ?? `https://${lead.domain}`}
                target="_blank"
                rel="noreferrer"
                className="inline-flex items-center gap-1 hover:underline"
              >
                {lead.signals.has_ssl ? <Lock className="size-3" /> : <Globe className="size-3" />}
                {lead.domain}
              </a>
            ) : (
              <span className="inline-flex items-center gap-1">
                <Users className="size-3" /> no website on file
              </span>
            )}
          </SheetDescription>
        </SheetHeader>
        {isLoading && (
          <div className="space-y-3 px-4">
            <Skeleton className="h-8 w-32" />
            <Skeleton className="h-40 w-full" />
          </div>
        )}
        {lead && <Body lead={lead} />}
      </SheetContent>
    </Sheet>
  );
}
