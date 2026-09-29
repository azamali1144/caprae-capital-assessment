"use client";

import { LayoutDashboard, SlidersHorizontal, Upload, Users } from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";

import { cn } from "@/lib/utils";

const NAV = [
  { href: "/", label: "Dashboard", icon: LayoutDashboard },
  { href: "/leads", label: "Leads", icon: Users },
  { href: "/imports", label: "Imports", icon: Upload },
  { href: "/settings/icp", label: "ICP Settings", icon: SlidersHorizontal },
];

export function Sidebar() {
  const pathname = usePathname();

  return (
    <aside className="hidden w-56 shrink-0 border-r bg-sidebar md:flex md:flex-col">
      <Link href="/" className="flex h-14 items-center gap-2 border-b px-4">
        <span className="grid size-7 place-items-center rounded-md bg-primary text-sm font-bold text-primary-foreground">
          L
        </span>
        <span className="font-semibold tracking-tight">LeadLens</span>
      </Link>

      <nav className="flex flex-1 flex-col gap-1 p-2">
        {NAV.map(({ href, label, icon: Icon }) => {
          const active = href === "/" ? pathname === "/" : pathname.startsWith(href);
          return (
            <Link
              key={href}
              href={href}
              className={cn(
                "flex items-center gap-2 rounded-md px-3 py-2 text-sm text-sidebar-foreground/80 transition-colors hover:bg-sidebar-accent hover:text-sidebar-foreground",
                active && "bg-sidebar-accent font-medium text-sidebar-foreground",
              )}
            >
              <Icon className="size-4" />
              {label}
            </Link>
          );
        })}
      </nav>

      <p className="p-4 text-xs text-muted-foreground">
        Import → Enrich → Act
      </p>
    </aside>
  );
}

export { NAV };
