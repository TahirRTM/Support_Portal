"use client";
import { useParams } from "next/navigation";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { api } from "@/lib/api";
import { Button, Textarea, StatusBadge } from "@/components/ui/primitives";

interface AdminMessage { id: string; author_type: string; author_display: string; visibility: string; body: string; created_at: string; }
interface Detail {
  id: string; case_number: string; subject: string; status: string; description: string;
  client_name: string; client_email: string; client_company: string | null; client_phone: string | null;
  messages: AdminMessage[];
}
const STATUSES = ["new","open","in_progress","pending_client","pending_internal","resolved","closed","reopened"];

export default function AdminTicketDetail() {
  const { id } = useParams<{ id: string }>();
  const qc = useQueryClient();
  const [body, setBody] = useState("");
  const [internal, setInternal] = useState(false);

  const { data, isLoading, isError } = useQuery({
    queryKey: ["ticket", id],
    queryFn: () => api<Detail>(`/admin/tickets/${id}`, { auth: true }),
  });

  const send = useMutation({
    mutationFn: () => api(`/admin/tickets/${id}/messages`, { method: "POST", auth: true, body: JSON.stringify({ body, internal }) }),
    onSuccess: () => { setBody(""); toast.success(internal ? "Internal note added" : "Reply sent"); qc.invalidateQueries({ queryKey: ["ticket", id] }); },
    onError: (e: Error) => toast.error(e.message),
  });
  const setStatus = useMutation({
    mutationFn: (status: string) => api(`/admin/tickets/${id}/status`, { method: "POST", auth: true, body: JSON.stringify({ status }) }),
    onSuccess: () => { toast.success("Status updated"); qc.invalidateQueries({ queryKey: ["ticket", id] }); },
    onError: (e: Error) => toast.error(e.message),
  });

  if (isLoading) return <main className="p-8 text-neutral-500">Loading...</main>;
  if (isError || !data) return <main className="p-8 text-red-600">Sign in required (/admin/login).</main>;

  return (
    <main className="p-8">
      <div className="flex items-start justify-between">
        <div>
          <div className="font-mono text-xs text-neutral-500">{data.case_number}</div>
          <h1 className="mt-1 text-2xl font-semibold">{data.subject}</h1>
          <p className="mt-1 text-sm text-neutral-500">{data.client_name} · {data.client_email}{data.client_company ? ` · ${data.client_company}` : ""}</p>
        </div>
        <div className="flex items-center gap-2">
          <StatusBadge status={data.status} />
          <select className="rounded-md border border-neutral-300 dark:border-neutral-700 bg-transparent px-2 py-1 text-sm"
            value={data.status} onChange={(e) => setStatus.mutate(e.target.value)}>
            {STATUSES.map(s => <option key={s} value={s}>{s}</option>)}
          </select>
        </div>
      </div>

      <section className="mt-8 space-y-3">
        {data.messages.map((m) => (
          <div key={m.id} className={"rounded-lg border p-4 " + (m.visibility === "internal"
            ? "border-amber-300 bg-amber-50 dark:border-amber-800 dark:bg-amber-950/30"
            : "border-neutral-200 dark:border-neutral-800")}>
            <div className="flex justify-between text-xs text-neutral-500">
              <span className="font-medium">{m.author_display} ({m.author_type}){m.visibility === "internal" ? " · INTERNAL" : ""}</span>
              <span>{new Date(m.created_at).toLocaleString()}</span>
            </div>
            <p className="mt-2 whitespace-pre-wrap text-sm">{m.body}</p>
          </div>
        ))}
      </section>

      <section className="mt-8">
        <Textarea rows={4} value={body} onChange={(e) => setBody(e.target.value)} placeholder={internal ? "Internal note (never shown to the client)" : "Public reply to the client"} />
        <div className="mt-3 flex items-center gap-4">
          <label className="flex items-center gap-2 text-sm">
            <input type="checkbox" checked={internal} onChange={(e) => setInternal(e.target.checked)} /> Internal note
          </label>
          <Button disabled={!body.trim() || send.isPending} onClick={() => send.mutate()}>
            {send.isPending ? "Sending..." : internal ? "Add note" : "Send reply"}
          </Button>
        </div>
      </section>
    </main>
  );
}
