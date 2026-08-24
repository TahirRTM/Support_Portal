"use client";
import { useQuery } from "@tanstack/react-query";
import Link from "next/link";
import { useState } from "react";
import { api } from "@/lib/api";
import type { Page, AdminTicketRow } from "@/types";
import { Input, StatusBadge } from "@/components/ui/primitives";

export default function AdminTickets() {
  const [q, setQ] = useState("");
  const [status, setStatus] = useState("");
  const { data, isLoading, isError } = useQuery({
    queryKey: ["tickets", q, status],
    queryFn: () => api<Page<AdminTicketRow>>(
      `/admin/tickets?${new URLSearchParams({ ...(q ? { q } : {}), ...(status ? { status } : {}) })}`,
      { auth: true }),
  });

  return (
    <main className="p-8">
      <h1 className="text-2xl font-semibold">Tickets</h1>
      <div className="mt-4 flex gap-3">
        <Input placeholder="Search case, subject, email..." value={q} onChange={(e) => setQ(e.target.value)} className="max-w-sm" />
        <select className="rounded-md border border-neutral-300 dark:border-neutral-700 bg-transparent px-3 text-sm" value={status} onChange={(e) => setStatus(e.target.value)}>
          <option value="">All statuses</option>
          {["new","open","in_progress","pending_client","resolved","closed"].map(s => <option key={s} value={s}>{s}</option>)}
        </select>
      </div>

      <div className="mt-6 overflow-hidden rounded-lg border border-neutral-200 dark:border-neutral-800">
        <table className="w-full text-sm">
          <thead className="bg-neutral-100 dark:bg-neutral-900 text-left">
            <tr><th className="p-3">Case</th><th className="p-3">Subject</th><th className="p-3">Client</th><th className="p-3">Status</th><th className="p-3">SLA</th></tr>
          </thead>
          <tbody>
            {isLoading && <tr><td colSpan={5} className="p-6 text-center text-neutral-500">Loading...</td></tr>}
            {isError && <tr><td colSpan={5} className="p-6 text-center text-red-600">Sign in required (/admin/login).</td></tr>}
            {data?.items.length === 0 && <tr><td colSpan={5} className="p-6 text-center text-neutral-500">No tickets match.</td></tr>}
            {data?.items.map((t) => (
              <tr key={t.id} className="border-t border-neutral-200 dark:border-neutral-800 hover:bg-neutral-50 dark:hover:bg-neutral-900">
                <td className="p-3 font-mono text-xs"><Link className="text-brand underline" href={`/admin/tickets/${t.id}`}>{t.case_number}</Link></td>
                <td className="p-3">{t.subject}</td>
                <td className="p-3 text-neutral-500">{t.client_email}</td>
                <td className="p-3"><StatusBadge status={t.status} /></td>
                <td className="p-3">{(t.sla_response_breached || t.sla_resolution_breached) ? <span className="text-red-600">Breached</span> : "OK"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
      {data && <p className="mt-3 text-xs text-neutral-500">{data.total} total</p>}
    </main>
  );
}
