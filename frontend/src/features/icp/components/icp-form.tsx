"use client";

import { zodResolver } from "@hookform/resolvers/zod";
import { Briefcase, Target } from "lucide-react";
import { Controller, useForm } from "react-hook-form";
import { z } from "zod";

import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { cn } from "@/lib/utils";

import type { IcpMode, IcpProfile, IcpProfileInput } from "../types";
import { TagInput } from "./tag-input";

const optionalInt = z
  .union([z.string(), z.number(), z.null()])
  .transform((v) => (v === "" || v === null ? null : Number(v)))
  .refine((v) => v === null || (Number.isInteger(v) && v >= 0), "Whole number, 0 or more");

const schema = z
  .object({
    name: z.string().trim().min(1, "Give it a name"),
    mode: z.enum(["sales", "acquisition"]),
    industries: z.array(z.string()),
    countries: z.array(z.string()),
    employee_min: optionalInt,
    employee_max: optionalInt,
    min_years_in_business: optionalInt,
  })
  .refine(
    (v) => v.employee_min === null || v.employee_max === null || v.employee_min <= v.employee_max,
    { message: "Min can't be bigger than max", path: ["employee_max"] },
  );

type FormIn = z.input<typeof schema>;
type FormOut = z.output<typeof schema>;

export const MODES: Record<IcpMode, { label: string; icon: typeof Target; blurb: string }> = {
  sales: {
    label: "Sales",
    icon: Target,
    blurb:
      "You're selling to these companies. Rewards reachable decision makers, verified emails, hiring and modern tools.",
  },
  acquisition: {
    label: "Acquisition fit",
    icon: Briefcase,
    blurb:
      "You're looking to buy one (ETA / search fund). Rewards long-established, owner-run, 5-100 staff businesses - an older website counts as upside, not a flaw.",
  },
};

function toForm(p?: IcpProfile): FormIn {
  return {
    name: p?.name ?? "",
    mode: p?.mode ?? "sales",
    industries: p?.rules.industries ?? [],
    countries: p?.rules.countries ?? [],
    employee_min: p?.rules.employee_min ?? null,
    employee_max: p?.rules.employee_max ?? null,
    min_years_in_business: p?.rules.min_years_in_business ?? null,
  };
}

type Props = {
  profile?: IcpProfile;
  saving?: boolean;
  onSubmit: (input: IcpProfileInput) => void;
};

export function IcpForm({ profile, saving, onSubmit }: Props) {
  const form = useForm<FormIn, unknown, FormOut>({
    resolver: zodResolver(schema),
    values: toForm(profile),
  });
  const { register, control, handleSubmit, formState } = form;
  const err = formState.errors;

  function submit(v: FormOut) {
    onSubmit({
      name: v.name,
      mode: v.mode,
      rules: {
        ...(profile?.rules ?? {}), // keep things the form doesn't edit (weights etc)
        industries: v.industries,
        countries: v.countries,
        employee_min: v.employee_min,
        employee_max: v.employee_max,
        min_years_in_business: v.min_years_in_business,
      },
    });
  }

  return (
    <form onSubmit={handleSubmit(submit)} className="space-y-5">
      <div className="space-y-1.5">
        <Label htmlFor="icp-name">Profile name</Label>
        <Input id="icp-name" {...register("name")} />
        {err.name && <p className="text-xs text-destructive">{err.name.message}</p>}
      </div>

      <Controller
        control={control}
        name="mode"
        render={({ field }) => (
          <div className="space-y-1.5">
            <Label>Scoring lens</Label>
            <div className="grid gap-2 sm:grid-cols-2">
              {(Object.keys(MODES) as IcpMode[]).map((m) => {
                const { label, icon: Icon, blurb } = MODES[m];
                const on = field.value === m;
                return (
                  <button
                    key={m}
                    type="button"
                    onClick={() => field.onChange(m)}
                    className={cn(
                      "rounded-lg border p-3 text-left transition-colors",
                      on ? "border-primary bg-primary/5 ring-1 ring-primary" : "hover:bg-muted/50",
                    )}
                  >
                    <p className="flex items-center gap-2 text-sm font-medium">
                      <Icon className="size-4" /> {label}
                    </p>
                    <p className="mt-1 text-xs text-muted-foreground">{blurb}</p>
                  </button>
                );
              })}
            </div>
          </div>
        )}
      />

      <div className="space-y-1.5">
        <Label htmlFor="icp-industries">Target industries</Label>
        <Controller
          control={control}
          name="industries"
          render={({ field }) => (
            <TagInput
              id="icp-industries"
              value={field.value}
              onChange={field.onChange}
              placeholder="HVAC, Plumbing… (enter to add)"
            />
          )}
        />
      </div>

      <div className="space-y-1.5">
        <Label htmlFor="icp-countries">Countries / states</Label>
        <Controller
          control={control}
          name="countries"
          render={({ field }) => (
            <TagInput id="icp-countries" value={field.value} onChange={field.onChange} placeholder="US, CA…" />
          )}
        />
      </div>

      <div className="grid gap-4 sm:grid-cols-3">
        <div className="space-y-1.5">
          <Label htmlFor="emp-min">Min employees</Label>
          <Input id="emp-min" type="number" min={0} {...register("employee_min")} />
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="emp-max">Max employees</Label>
          <Input id="emp-max" type="number" min={0} {...register("employee_max")} />
          {err.employee_max && <p className="text-xs text-destructive">{err.employee_max.message}</p>}
        </div>
        <div className="space-y-1.5">
          <Label htmlFor="min-years">Min years in business</Label>
          <Input id="min-years" type="number" min={0} {...register("min_years_in_business")} />
        </div>
      </div>

      <div className="flex justify-end">
        <Button type="submit" disabled={saving || !formState.isDirty}>
          {saving ? "Saving…" : "Save changes"}
        </Button>
      </div>
    </form>
  );
}
