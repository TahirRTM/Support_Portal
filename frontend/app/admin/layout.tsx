"use client";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { cn } from "@/lib/utils";

const NAV = [
  ["/admin", "Dashboard"], ["/admin/tickets", "Tickets"],
  ["/admin/users", "Users"], ["/admin/roles", "Roles"],
  ["/admin/departments", "Departments"], ["/admin/teams", "Teams"],
  ["/admin/categories", "Categories"], ["/admin/sla", "SLA"],
  ["/admin/notifications", "Notifications"], ["/admin/knowledge-base", "Knowledge Base"],
  ["/admin/analytics", "Analytics"], ["/admin/audit-logs", "Audit Logs"],
  ["/admin/settings", "Settings"],
] as const;

export default function AdminLayout({ children }: { children: React.ReactNode }) {
  const path = usePathname();
  if (path === "/admin/login") return <>{children}</>;
  return (
    <div className="grid min-h-screen grid-cols-[240px_1fr]">
      <aside className="border-r border-neutral-200 dark:border-neutral-800 p-4">
        <div className="px-2 text-sm font-semibold">AI Support Portal</div>
        <nav className="mt-6 space-y-1">
          {NAV.map(([href, label]) => (
            <Link key={href} href={href} className={cn(
              "block rounded-md px-3 py-2 text-sm",
              path === href ? "bg-brand text-brand-fg" : "hover:bg-neutral-100 dark:hover:bg-neutral-900",
            )}>{label}</Link>
          ))}
        </nav>
      </aside>
      <div className="overflow-auto">{children}</div>
    </div>
  );
}
