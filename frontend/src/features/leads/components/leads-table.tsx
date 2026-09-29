"use client";

import {
  type ColumnDef,
  type RowSelectionState,
  flexRender,
  getCoreRowModel,
  useReactTable,
} from "@tanstack/react-table";
import { ArrowDown, ArrowUp, ArrowUpDown, ChevronLeft, ChevronRight, Crown } from "lucide-react";

import { EmailStatusIcon } from "@/components/shared/email-status-icon";
import { ScoreBadge } from "@/components/shared/score-badge";
import { StatusChip } from "@/components/shared/status-chip";
import { Button } from "@/components/ui/button";
import { Checkbox } from "@/components/ui/checkbox";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { cn } from "@/lib/utils";

import type { Lead, LeadFilters } from "../types";

type SortKey = NonNullable<LeadFilters["sort"]>;

function timeAgo(iso: string | null) {
  if (!iso) return "—";
  const mins = Math.round((Date.now() - new Date(iso).getTime()) / 60000);
  if (mins < 1) return "just now";
  if (mins < 60) return `${mins}m ago`;
  if (mins < 60 * 24) return `${Math.round(mins / 60)}h ago`;
  return `${Math.round(mins / 1440)}d ago`;
}

function Favicon({ domain }: { domain: string | null }) {
  if (!domain) return <div className="size-5 shrink-0 rounded bg-muted" />;
  return (
    // eslint-disable-next-line @next/next/no-img-element -- tiny external icon, next/image is overkill
    <img
      src={`https://www.google.com/s2/favicons?domain=${domain}&sz=32`}
      alt=""
      className="size-5 shrink-0 rounded"
      loading="lazy"
    />
  );
}

function buildColumns(): ColumnDef<Lead>[] {
  return [
    {
      id: "select",
      header: ({ table }) => (
        <Checkbox
          aria-label="Select all on this page"
          checked={table.getIsAllPageRowsSelected()}
          indeterminate={table.getIsSomePageRowsSelected()}
          onCheckedChange={(v) => table.toggleAllPageRowsSelected(!!v)}
        />
      ),
      cell: ({ row }) => (
        <Checkbox
          aria-label="Select lead"
          checked={row.getIsSelected()}
          onCheckedChange={(v) => row.toggleSelected(!!v)}
          onClick={(e) => e.stopPropagation()}
        />
      ),
      size: 36,
    },
    {
      id: "name",
      header: "Company",
      meta: { sort: "name" },
      cell: ({ row: { original: l } }) => (
        <div className="flex min-w-0 items-center gap-2.5">
          <Favicon domain={l.domain} />
          <div className="min-w-0">
            <p className="truncate font-medium">{l.name}</p>
            <p className="truncate text-xs text-muted-foreground">{l.domain ?? "no website"}</p>
          </div>
        </div>
      ),
    },
    {
      id: "score",
      header: "Score",
      meta: { sort: "score" },
      cell: ({ row: { original: l } }) => (
        <ScoreBadge score={l.score} grade={l.grade} reasons={l.top_reasons} />
      ),
    },
    {
      id: "industry",
      header: "Industry",
      cell: ({ row }) => <span className="text-sm">{row.original.industry ?? "—"}</span>,
    },
    {
      id: "location",
      header: "Location",
      cell: ({ row: { original: l } }) => (
        <span className="text-sm text-muted-foreground">
          {[l.city, l.state, l.country].filter(Boolean).join(", ") || "—"}
        </span>
      ),
    },
    {
      id: "contact",
      header: "Best contact",
      cell: ({ row: { original: l } }) => {
        const c = l.best_contact;
        if (!c) return <span className="text-sm text-muted-foreground">—</span>;
        return (
          <div className="flex min-w-0 items-center gap-2">
            {c.email && <EmailStatusIcon status={c.email_status} role={c.email_type === "role"} />}
            <div className="min-w-0">
              <p className="flex items-center gap-1 truncate text-sm">
                {c.full_name ?? c.email ?? c.phone_e164}
                {c.is_decision_maker && <Crown className="size-3 text-amber-500" />}
              </p>
              {c.title && <p className="truncate text-xs text-muted-foreground">{c.title}</p>}
            </div>
          </div>
        );
      },
    },
    {
      id: "stage",
      header: "Stage",
      cell: ({ row }) => <StatusChip stage={row.original.stage} />,
    },
    {
      id: "last_enriched_at",
      header: "Enriched",
      meta: { sort: "last_enriched_at" },
      cell: ({ row }) => (
        <span className="text-xs whitespace-nowrap text-muted-foreground">
          {timeAgo(row.original.last_enriched_at)}
        </span>
      ),
    },
  ];
}

const columns = buildColumns();

type Props = {
  data: Lead[];
  total: number;
  page: number;
  pageSize: number;
  sort: SortKey;
  order: "asc" | "desc";
  loading?: boolean;
  selection: RowSelectionState;
  onSelectionChange: (s: RowSelectionState) => void;
  onSort: (sort: SortKey, order: "asc" | "desc") => void;
  onPage: (page: number) => void;
  onOpen: (id: string) => void;
};

export function LeadsTable(props: Props) {
  const { data, total, page, pageSize, sort, order, loading } = props;
  const pages = Math.max(1, Math.ceil(total / pageSize));

  // eslint-disable-next-line react-hooks/incompatible-library -- tanstack table isn't compiler-safe yet
  const table = useReactTable({
    data,
    columns,
    getRowId: (row) => row.id,
    getCoreRowModel: getCoreRowModel(),
    manualPagination: true,
    manualSorting: true,
    state: { rowSelection: props.selection },
    onRowSelectionChange: (updater) =>
      props.onSelectionChange(typeof updater === "function" ? updater(props.selection) : updater),
  });

  function headerFor(id: string, label: React.ReactNode, sortKey?: SortKey) {
    if (!sortKey) return label;
    const active = sort === sortKey;
    const Icon = !active ? ArrowUpDown : order === "asc" ? ArrowUp : ArrowDown;
    return (
      <button
        type="button"
        className={cn("inline-flex items-center gap-1 hover:text-foreground", active && "text-foreground")}
        onClick={() => props.onSort(sortKey, active && order === "desc" ? "asc" : "desc")}
      >
        {label}
        <Icon className="size-3.5" />
      </button>
    );
  }

  return (
    <div className="space-y-3">
      <div className={cn("overflow-hidden rounded-lg border transition-opacity", loading && "opacity-60")}>
        <div className="max-h-[calc(100vh-18rem)] overflow-auto">
          <Table>
            <TableHeader className="sticky top-0 z-10 bg-background shadow-[0_1px_0_var(--border)]">
              {table.getHeaderGroups().map((hg) => (
                <TableRow key={hg.id} className="hover:bg-transparent">
                  {hg.headers.map((h) => {
                    const sortKey = (h.column.columnDef.meta as { sort?: SortKey } | undefined)?.sort;
                    return (
                      <TableHead key={h.id} style={{ width: h.column.columnDef.size }}>
                        {headerFor(h.id, flexRender(h.column.columnDef.header, h.getContext()), sortKey)}
                      </TableHead>
                    );
                  })}
                </TableRow>
              ))}
            </TableHeader>
            <TableBody>
              {table.getRowModel().rows.map((row) => (
                <TableRow
                  key={row.id}
                  data-state={row.getIsSelected() ? "selected" : undefined}
                  className="cursor-pointer"
                  onClick={() => props.onOpen(row.original.id)}
                >
                  {row.getVisibleCells().map((cell) => (
                    <TableCell key={cell.id} className="max-w-64 py-2.5">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </TableCell>
                  ))}
                </TableRow>
              ))}
            </TableBody>
          </Table>
        </div>
      </div>

      <div className="flex items-center justify-between text-sm text-muted-foreground">
        <span>
          {total.toLocaleString()} lead{total === 1 ? "" : "s"}
          {Object.keys(props.selection).length > 0 &&
            ` · ${Object.keys(props.selection).length} selected`}
        </span>
        <div className="flex items-center gap-2">
          <span>
            Page {page} of {pages}
          </span>
          <Button
            variant="outline"
            size="icon-sm"
            aria-label="Previous page"
            disabled={page <= 1}
            onClick={() => props.onPage(page - 1)}
          >
            <ChevronLeft />
          </Button>
          <Button
            variant="outline"
            size="icon-sm"
            aria-label="Next page"
            disabled={page >= pages}
            onClick={() => props.onPage(page + 1)}
          >
            <ChevronRight />
          </Button>
        </div>
      </div>
    </div>
  );
}
