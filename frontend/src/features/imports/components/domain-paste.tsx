"use client";

import { useMemo, useState } from "react";

import { Button } from "@/components/ui/button";
import { Textarea } from "@/components/ui/textarea";

const MAX = 5000;

// accepts newlines, commas or spaces between domains
export function parseDomains(text: string): string[] {
  const seen = new Set<string>();
  for (const part of text.split(/[\s,;]+/)) {
    const d = part.trim().toLowerCase();
    if (d && d.includes(".")) seen.add(d);
  }
  return [...seen];
}

export function DomainPaste({ onSubmit, busy }: { onSubmit: (d: string[]) => void; busy?: boolean }) {
  const [text, setText] = useState("");
  const domains = useMemo(() => parseDomains(text), [text]);
  const tooMany = domains.length > MAX;

  return (
    <div className="space-y-3">
      <Textarea
        value={text}
        onChange={(e) => setText(e.target.value)}
        placeholder={"acmehvac.com\nhttps://www.brightplumbing.com\ncoolair.co"}
        className="min-h-48 font-mono text-sm"
      />
      <div className="flex items-center justify-between gap-3">
        <p className={tooMany ? "text-sm text-destructive" : "text-sm text-muted-foreground"}>
          {domains.length.toLocaleString()} unique domain{domains.length === 1 ? "" : "s"}
          {tooMany && ` · max ${MAX.toLocaleString()} per import`}
        </p>
        <Button disabled={!domains.length || tooMany || busy} onClick={() => onSubmit(domains)}>
          {busy ? "Starting…" : "Enrich domains"}
        </Button>
      </div>
    </div>
  );
}
