import { apiGet, apiPost, apiUpload } from "@/lib/api-client";

import type { ImportCreated, ImportJob } from "./types";

export const importsApi = {
  uploadCsv(file: File) {
    const form = new FormData();
    form.append("file", file);
    return apiUpload<ImportCreated>("/imports/csv", form);
  },
  importDomains(domains: string[]) {
    return apiPost<ImportCreated>("/imports/domains", { domains });
  },
  get(id: string) {
    return apiGet<ImportJob>(`/imports/${id}`);
  },
  recent(limit = 10) {
    return apiGet<ImportJob[]>("/imports", { limit });
  },
};
