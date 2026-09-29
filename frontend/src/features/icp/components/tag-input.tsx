"use client";

import { X } from "lucide-react";
import { useState } from "react";

import { Badge } from "@/components/ui/badge";
import { Input } from "@/components/ui/input";

type Props = {
  value: string[];
  onChange: (v: string[]) => void;
  placeholder?: string;
  id?: string;
};

// enter or comma adds a tag, backspace on empty removes the last one
export function TagInput({ value, onChange, placeholder, id }: Props) {
  const [draft, setDraft] = useState("");

  function add(raw: string) {
    const tags = raw
      .split(",")
      .map((t) => t.trim())
      .filter((t) => t && !value.some((v) => v.toLowerCase() === t.toLowerCase()));
    if (tags.length) onChange([...value, ...tags]);
    setDraft("");
  }

  return (
    <div className="flex min-h-9 flex-wrap items-center gap-1.5 rounded-lg border px-2 py-1.5 focus-within:ring-3 focus-within:ring-ring/50">
      {value.map((tag) => (
        <Badge key={tag} variant="secondary" className="gap-1">
          {tag}
          <button
            type="button"
            aria-label={`Remove ${tag}`}
            onClick={() => onChange(value.filter((t) => t !== tag))}
            className="opacity-60 hover:opacity-100"
          >
            <X className="size-3" />
          </button>
        </Badge>
      ))}
      <Input
        id={id}
        value={draft}
        onChange={(e) => setDraft(e.target.value)}
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === ",") {
            e.preventDefault();
            add(draft);
          } else if (e.key === "Backspace" && !draft && value.length) {
            onChange(value.slice(0, -1));
          }
        }}
        onBlur={() => draft && add(draft)}
        placeholder={value.length ? "" : placeholder}
        className="h-6 min-w-24 flex-1 border-0 p-0 shadow-none focus-visible:ring-0 dark:bg-transparent"
      />
    </div>
  );
}
