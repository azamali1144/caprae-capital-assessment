"use client";

import type { RowSelectionState } from "@tanstack/react-table";
import { Download, SearchX, Upload, Users } from "lucide-react";
import Link from "next/link";
import { Suspense, useState } from "react";

import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { TableSkeleton } from "@/components/shared/table-skeleton";
import { Button } from "@/components/ui/button";
import { leadsApi } from "@/features/leads/api";
import { BulkActionsBar } from "@/features/leads/components/bulk-actions-bar";
import { LeadDrawer } from "@/features/leads/components/lead-drawer";
import { LeadsFilters } from "@/features/leads/components/leads-filters";
import { LeadsTable } from "@/features/leads/components/leads-table";
import { useLeadFilters, useLeadSearchParams, useLeads } from "@/features/leads/hooks";

function LeadsWorkspace() {
  const filters = useLeadFilters();
  const [params, setParams] = useLeadSearchParams();
  const { data, isLoading, isFetching, error } = useLeads(filters);
  const [selection, setSelection] = useState<RowSelectionState>({});

  const hasFilters = Boolean(
    filters.q ||
      filters.grade?.length ||
      filters.min_score ||
      filters.industry ||
      filters.country ||
      filters.stage ||
      filters.email_status ||
      filters.import,
  );

  let content: React.ReactNode;
  if (isLoading) content = <TableSkeleton />;
  else if (error)
    content = <EmptyState icon={Users} title="Couldn't load leads" description={error.message} />;
  else if (!data?.total && hasFilters)
    content = (
      <EmptyState
        icon={SearchX}
        title="No leads match these filters"
        description="Try loosening the grade or score filters."
      />
    );
  else if (!data?.total)
    content = (
      <EmptyState
        icon={Upload}
        title="No leads yet"
        description="Import a SaaSquatch export or paste a few domains - we'll dedupe, enrich and rank them."
        action={<Button nativeButton={false} render={<Link href="/imports" />}>Import your first list</Button>}
      />
    );
  else
    content = (
      <LeadsTable
        data={data.items}
        total={data.total}
        page={data.page}
        pageSize={data.page_size}
        sort={filters.sort ?? "score"}
        order={filters.order ?? "desc"}
        loading={isFetching}
        selection={selection}
        onSelectionChange={setSelection}
        onSort={(sort, order) => setParams({ sort, order, page: 1 })}
        onPage={(page) => setParams({ page })}
        onOpen={(lead) => setParams({ lead })}
      />
    );

  return (
    <>
      <div className="mb-2 flex justify-end">
        <Button
          variant="outline"
          size="sm"
          disabled={!data?.total}
          nativeButton={false}
          render={<a href={leadsApi.exportUrl(filters)} download />}
        >
          <Download /> Export {data?.total ? data.total.toLocaleString() : ""} to CSV
        </Button>
      </div>
      <LeadsFilters />
      {content}
      <LeadDrawer id={params.lead} onClose={() => setParams({ lead: null })} />
      <BulkActionsBar ids={Object.keys(selection)} onDone={() => setSelection({})} />
    </>
  );
}

export default function LeadsPage() {
  return (
    <div>
      <PageHeader
        title="Leads"
        description="Step 2 of 3 - ranked by score. Click a row to see exactly why."
      />
      <Suspense fallback={<TableSkeleton />}>
        <LeadsWorkspace />
      </Suspense>
    </div>
  );
}
