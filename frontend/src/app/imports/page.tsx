"use client";

import { FileUp, ListPlus } from "lucide-react";
import { useState } from "react";
import { toast } from "sonner";

import { PageHeader } from "@/components/shared/page-header";
import { Card, CardContent } from "@/components/ui/card";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { DomainPaste } from "@/features/imports/components/domain-paste";
import { JobProgress } from "@/features/imports/components/job-progress";
import { RecentImports } from "@/features/imports/components/recent-imports";
import { UploadDropzone } from "@/features/imports/components/upload-dropzone";
import { useCreateImport } from "@/features/imports/hooks";

export default function ImportsPage() {
  const createImport = useCreateImport();
  const [active, setActive] = useState<{ id: string; warnings: string[] } | null>(null);

  function start(input: { file: File } | { domains: string[] }) {
    createImport.mutate(input, {
      onSuccess: (res) => {
        setActive({ id: res.job_id, warnings: res.warnings });
        if (res.unmapped_columns.length) {
          toast.info(`Ignored ${res.unmapped_columns.length} unknown column(s)`, {
            description: res.unmapped_columns.slice(0, 5).join(", "),
          });
        }
      },
      onError: (err) => toast.error("Import didn't start", { description: err.message }),
    });
  }

  return (
    <div className="mx-auto max-w-3xl">
      <PageHeader
        title="Import leads"
        description="Step 1 of 3 - bring in a list, we'll dedupe it, crawl each company's site and score it."
      />

      <div className="space-y-6">
        <Card>
          <CardContent>
            <Tabs defaultValue="csv">
              <TabsList className="mb-4">
                <TabsTrigger value="csv">
                  <FileUp className="size-4" /> Upload CSV
                </TabsTrigger>
                <TabsTrigger value="domains">
                  <ListPlus className="size-4" /> Paste domains
                </TabsTrigger>
              </TabsList>
              <TabsContent value="csv">
                <UploadDropzone busy={createImport.isPending} onSubmit={(file) => start({ file })} />
              </TabsContent>
              <TabsContent value="domains">
                <DomainPaste
                  busy={createImport.isPending}
                  onSubmit={(domains) => start({ domains })}
                />
              </TabsContent>
            </Tabs>
          </CardContent>
        </Card>

        {active && <JobProgress key={active.id} jobId={active.id} warnings={active.warnings} />}

        <section>
          <h2 className="mb-3 text-sm font-medium text-muted-foreground">Recent imports</h2>
          <RecentImports />
        </section>
      </div>
    </div>
  );
}
