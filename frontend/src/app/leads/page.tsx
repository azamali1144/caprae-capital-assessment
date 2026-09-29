"use client";

import type { RowSelectionState } from "@tanstack/react-table";
import { Upload, Users } from "lucide-react";
import Link from "next/link";
import { Suspense, useState } from "react";

import { EmptyState } from "@/components/shared/empty-state";
import { PageHeader } from "@/components/shared/page-header";
import { TableSkeleton } from "@/components/shared/table-skeleton";
import { Button } from "@/components/ui/button";
import { LeadsTable } from "@/features/leads/components/leads-table";
import { useLeadFilters, useLeadSearchParams, useLeads } from "@/features/leads/hooks";

function LeadsWorkspace() {
  const filters = useLeadFilters();
  const [, setParams] = useLeadSearchParams();
  const { data, isLoading, isFetching, error } = useLeads(filters);
  const [selection, setSelection] = useState<RowSelectionState>({});

  if (isLoading) return <TableSkeleton />;
  if (error) {
    return <EmptyState icon={Users} title="Couldn't load leads" description={error.message} />;
  }
  if (!data?.total) {
    return (
      <EmptyState
        icon={Upload}
        title="No leads yet"
        description="Import a SaaSquatch export or paste a few domains - we'll dedupe, enrich and rank them."
        action={<Button nativeButton={false} render={<Link href="/imports" />}>Import your first list</Button>}
      />
    );
  }

  return (
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
}

export default function LeadsPage() {
  return (
    <div>
      <PageHeader
        title="Leads"
        description="Step 2 of 3 - ranked by score. Hover a score to see why."
      />
      <Suspense fallback={<TableSkeleton />}>
        <LeadsWorkspace />
      </Suspense>
    </div>
  );
}
