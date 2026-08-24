"use client";
import { useQuery } from "@tanstack/react-query";
import { api } from "@/lib/api";
import type { Page, AdminTicketRow } from "@/types";

function useCount(params: string) {
  return useQuery({
    queryKey: ["count", params],
    queryFn: () => api<Page<AdminTicketRow>>(`/admin/tickets?page_size=1&${params}`, { auth: true }),
  });
}

export default function Dashboard() {
  const all = useCount("");
  const open = useCount("status=open");
  const pending = useCount("status=pending_client");
  const resolved = useCount("status=resolved");
  const overdue = useCount("overdue=true");
  const unassigned = useCount("unassigned=true");

  const cards: [string, ReturnType<typeof useCount>][] = [
    ["Total", all], ["Open", open], ["Pending client", pending],
    ["Resolved", resolved], ["SLA overdue", overdue], ["Unassigned", unassigned],
  ];

  return (
    <main className="p-8">
      <h1 className="text-2xl font-semibold">Dashboard</h1>
      <div className="mt-6 grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
        {cards.map(([label, q]) => (
          <div key={label} className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-5">
            <div className="text-sm text-neutral-500">{label}</div>
            <div className="mt-2 text-3xl font-semibold tabular-nums">
              {q.isLoading ? "—" : q.isError ? "?" : q.data?.total ?? 0}
            </div>
          </div>
        ))}
      </div>
      {all.isError && <p className="mt-6 text-sm text-red-600">Sign in required. Go to /admin/login.</p>}
    </main>
  );
}
