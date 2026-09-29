"use client";

import { Briefcase, Search, Sparkles, X } from "lucide-react";
import { useEffect, useState } from "react";

import { GRADE_STYLES } from "@/components/shared/score-badge";
import { stageLabel } from "@/components/shared/status-chip";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { Slider } from "@/components/ui/slider";
import { cn } from "@/lib/utils";

import { useLeadSearchParams } from "../hooks";
import { GRADES, STAGES, type EmailStatus, type Grade, type Stage } from "../types";

const EMAIL_OPTIONS: { value: EmailStatus; label: string }[] = [
  { value: "valid_mx", label: "Verified (MX)" },
  { value: "no_mx", label: "No mail server" },
  { value: "unknown", label: "Unverified" },
];

const ANY = "__any";

function useDebounced<T>(value: T, ms = 300) {
  const [v, setV] = useState(value);
  useEffect(() => {
    const t = setTimeout(() => setV(value), ms);
    return () => clearTimeout(t);
  }, [value, ms]);
  return v;
}

export function LeadsFilters() {
  const [p, setParams] = useLeadSearchParams();
  const [search, setSearch] = useState(p.q);
  const debounced = useDebounced(search);

  useEffect(() => {
    if (debounced !== p.q) setParams({ q: debounced || null, page: 1 });
  }, [debounced, p.q, setParams]);

  const set = (patch: Parameters<typeof setParams>[0]) => setParams({ ...patch, page: 1 });

  const toggleGrade = (g: Grade) =>
    set({ grade: p.grade.includes(g) ? p.grade.filter((x) => x !== g) : [...p.grade, g] });

  const dirty =
    !!p.q ||
    p.grade.length > 0 ||
    p.min_score > 0 ||
    !!p.industry ||
    !!p.country ||
    !!p.stage ||
    !!p.email_status ||
    !!p.import;

  function clearAll() {
    setSearch("");
    set({
      q: null,
      grade: null,
      min_score: null,
      industry: null,
      country: null,
      stage: null,
      email_status: null,
      import: null,
    });
  }

  return (
    <div className="mb-4 space-y-3">
      {/* quick presets for the two main jobs-to-be-done */}
      <div className="flex flex-wrap items-center gap-2">
        <span className="text-xs text-muted-foreground">Quick views:</span>
        <Button
          variant="outline"
          size="sm"
          onClick={() => set({ grade: ["A", "B"], email_status: "valid_mx", sort: "score", order: "desc" })}
        >
          <Sparkles className="text-indigo-500" /> Top prospects
        </Button>
        <Button
          variant="outline"
          size="sm"
          onClick={() => set({ grade: ["A"], sort: "founded_year", order: "asc" })}
          title="Best when the Acquisition-fit ICP is active"
        >
          <Briefcase className="text-violet-500" /> Acquisition targets
        </Button>
      </div>

      <div className="flex flex-wrap items-center gap-2">
        <div className="relative w-full sm:w-64">
          <Search className="pointer-events-none absolute top-1/2 left-2.5 size-4 -translate-y-1/2 text-muted-foreground" />
          <Input
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            placeholder="Search company or domain…"
            className="pl-8"
          />
        </div>

        <div className="flex items-center gap-1" role="group" aria-label="Grade">
          {GRADES.map((g) => {
            const on = p.grade.includes(g);
            return (
              <button
                key={g}
                type="button"
                aria-pressed={on}
                onClick={() => toggleGrade(g)}
                className={cn(
                  "h-8 w-8 rounded-md border text-sm font-semibold transition-colors",
                  on ? cn(GRADE_STYLES[g], "ring-1 ring-inset") : "text-muted-foreground hover:bg-muted",
                )}
              >
                {g}
              </button>
            );
          })}
        </div>

        <div className="flex w-44 items-center gap-2 px-1">
          <span className="text-xs whitespace-nowrap text-muted-foreground">Min {p.min_score}</span>
          <Slider
            value={[p.min_score]}
            min={0}
            max={100}
            step={5}
            onValueCommitted={(v) => set({ min_score: (Array.isArray(v) ? v[0] : v) || null })}
          />
        </div>

        <Select
          value={p.stage ?? ANY}
          onValueChange={(v) => set({ stage: v === ANY ? null : (v as Stage) })}
        >
          <SelectTrigger className="w-36">
            <SelectValue>{(v: string) => (v === ANY ? "Any stage" : stageLabel(v as Stage))}</SelectValue>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ANY}>Any stage</SelectItem>
            {STAGES.map((s) => (
              <SelectItem key={s} value={s}>
                {stageLabel(s)}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Select
          value={p.email_status ?? ANY}
          onValueChange={(v) => set({ email_status: v === ANY ? null : (v as EmailStatus) })}
        >
          <SelectTrigger className="w-40">
            <SelectValue>
              {(v: string) =>
                v === ANY ? "Any email" : EMAIL_OPTIONS.find((o) => o.value === v)?.label
              }
            </SelectValue>
          </SelectTrigger>
          <SelectContent>
            <SelectItem value={ANY}>Any email</SelectItem>
            {EMAIL_OPTIONS.map((o) => (
              <SelectItem key={o.value} value={o.value}>
                {o.label}
              </SelectItem>
            ))}
          </SelectContent>
        </Select>

        <Input
          defaultValue={p.industry}
          onBlur={(e) => e.target.value !== p.industry && set({ industry: e.target.value || null })}
          onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
          placeholder="Industry"
          className="w-32"
        />
        <Input
          defaultValue={p.country}
          onBlur={(e) => e.target.value !== p.country && set({ country: e.target.value || null })}
          onKeyDown={(e) => e.key === "Enter" && e.currentTarget.blur()}
          placeholder="Country"
          className="w-24"
        />

        {dirty && (
          <Button variant="ghost" size="sm" onClick={clearAll}>
            <X /> Clear filters
          </Button>
        )}
      </div>

      {p.import && (
        <p className="text-xs text-muted-foreground">
          Showing leads from one import ·{" "}
          <button type="button" className="underline" onClick={() => set({ import: null })}>
            show all
          </button>
        </p>
      )}
    </div>
  );
}
