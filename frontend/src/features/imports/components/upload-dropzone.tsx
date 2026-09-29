"use client";

import { FileSpreadsheet, UploadCloud, X } from "lucide-react";
import { useRef, useState } from "react";

import { Button } from "@/components/ui/button";
import { cn } from "@/lib/utils";

const MAX_MB = 5;

type Props = {
  onSubmit: (file: File) => void;
  busy?: boolean;
};

export function UploadDropzone({ onSubmit, busy }: Props) {
  const inputRef = useRef<HTMLInputElement>(null);
  const [file, setFile] = useState<File | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [dragging, setDragging] = useState(false);

  function pick(f: File | undefined) {
    setError(null);
    if (!f) return;
    if (!/\.(csv|txt)$/i.test(f.name)) return setError("That doesn't look like a .csv file.");
    if (f.size > MAX_MB * 1024 * 1024) return setError(`Keep it under ${MAX_MB} MB (5,000 rows).`);
    setFile(f);
  }

  return (
    <div className="space-y-3">
      <div
        role="button"
        tabIndex={0}
        onClick={() => inputRef.current?.click()}
        onKeyDown={(e) => (e.key === "Enter" || e.key === " ") && inputRef.current?.click()}
        onDragOver={(e) => {
          e.preventDefault();
          setDragging(true);
        }}
        onDragLeave={() => setDragging(false)}
        onDrop={(e) => {
          e.preventDefault();
          setDragging(false);
          pick(e.dataTransfer.files?.[0]);
        }}
        className={cn(
          "flex cursor-pointer flex-col items-center justify-center rounded-xl border-2 border-dashed px-6 py-10 text-center transition-colors outline-none focus-visible:ring-3 focus-visible:ring-ring/50",
          dragging ? "border-primary bg-primary/5" : "hover:border-primary/50 hover:bg-muted/40",
        )}
      >
        <UploadCloud className="mb-3 size-8 text-muted-foreground" />
        <p className="font-medium">Drop your SaaSquatch export here</p>
        <p className="mt-1 text-sm text-muted-foreground">
          or click to browse · any CSV with a website or company name column works
        </p>
        <input
          ref={inputRef}
          type="file"
          accept=".csv,text/csv"
          className="hidden"
          onChange={(e) => pick(e.target.files?.[0])}
        />
      </div>

      {error && <p className="text-sm text-destructive">{error}</p>}

      {file && (
        <div className="flex items-center gap-3 rounded-lg border bg-muted/30 px-3 py-2">
          <FileSpreadsheet className="size-5 text-primary" />
          <div className="min-w-0 flex-1">
            <p className="truncate text-sm font-medium">{file.name}</p>
            <p className="text-xs text-muted-foreground">{(file.size / 1024).toFixed(1)} KB</p>
          </div>
          <Button variant="ghost" size="icon-sm" aria-label="Remove file" onClick={() => setFile(null)}>
            <X />
          </Button>
        </div>
      )}

      <div className="flex items-center justify-between gap-3">
        <a
          href="/leadlens-template.csv"
          download
          className="text-sm text-muted-foreground underline-offset-4 hover:text-foreground hover:underline"
        >
          Download a template CSV
        </a>
        <Button disabled={!file || busy} onClick={() => file && onSubmit(file)}>
          {busy ? "Uploading…" : "Import & enrich"}
        </Button>
      </div>
    </div>
  );
}
