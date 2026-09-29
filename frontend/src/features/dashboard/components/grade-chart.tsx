"use client";

import { useRouter } from "next/navigation";
import { Bar, BarChart, Cell, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";

import { GRADE_LABEL } from "@/components/shared/score-badge";
import type { Grade } from "@/features/leads/types";

const FILL: Record<Grade, string> = {
  A: "var(--color-grade-a)",
  B: "var(--color-grade-b)",
  C: "var(--color-grade-c)",
  D: "var(--color-grade-d)",
};

export function GradeChart({ distribution }: { distribution: Record<Grade, number> }) {
  const router = useRouter();
  const data = (Object.keys(FILL) as Grade[]).map((g) => ({
    grade: g,
    label: `${g} · ${GRADE_LABEL[g]}`,
    count: distribution[g] ?? 0,
  }));

  return (
    <div className="h-56 w-full">
      <ResponsiveContainer>
        <BarChart data={data} margin={{ left: -20, right: 8, top: 8 }}>
          <XAxis dataKey="grade" tickLine={false} axisLine={false} fontSize={12} />
          <YAxis allowDecimals={false} tickLine={false} axisLine={false} fontSize={12} />
          <Tooltip
            cursor={{ fill: "var(--muted)" }}
            contentStyle={{
              background: "var(--popover)",
              border: "1px solid var(--border)",
              borderRadius: 8,
              fontSize: 12,
            }}
            labelFormatter={(_, p) => p?.[0]?.payload?.label}
            formatter={(v) => [v, "leads"]}
          />
          <Bar
            dataKey="count"
            radius={[6, 6, 0, 0]}
            isAnimationActive={false}
            className="cursor-pointer"
            // click a bar -> leads filtered to that grade
            onClick={(d) => router.push(`/leads?grade=${(d as unknown as { grade: Grade }).grade}`)}
          >
            {data.map((d) => (
              <Cell key={d.grade} fill={FILL[d.grade]} />
            ))}
          </Bar>
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
