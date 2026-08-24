"use client";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { useState } from "react";
import { toast } from "sonner";
import { clientApi } from "@/lib/api";
import type { ClientTicketView } from "@/types";
import { Button, Textarea, StatusBadge } from "@/components/ui/primitives";
import { STATUS_LABEL } from "@/lib/utils";

export default function CaseDetail() {
  const qc = useQueryClient();
  const [reply, setReply] = useState("");
  const { data, isLoading, isError, error } = useQuery({
    queryKey: ["my-ticket"],
    queryFn: () => clientApi<ClientTicketView>("/support/tickets/me"),
    retry: false,
  });

  const sendReply = useMutation({
    mutationFn: () => clientApi("/support/tickets/me/reply", { method: "POST", body: JSON.stringify({ body: reply }) }),
    onSuccess: () => { setReply(""); toast.success("Reply sent"); qc.invalidateQueries({ queryKey: ["my-ticket"] }); },
    onError: (e: Error) => toast.error(e.message),
  });

  if (isLoading) return <Skeleton />;
  if (isError) return (
    <main className="mx-auto max-w-2xl px-6 py-20 text-center">
      <h1 className="text-2xl font-semibold">Session expired</h1>
      <p className="mt-2 text-neutral-500">{(error as Error).message}. Please verify again.</p>
      <a className="mt-6 inline-block text-brand underline" href="/support/track">Back to tracking</a>
    </main>
  );
  if (!data) return null;

  return (
    <main className="mx-auto max-w-3xl px-6 py-16">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-mono text-sm text-neutral-500">{data.case_number}</div>
          <h1 className="mt-1 text-2xl font-semibold">{data.subject}</h1>
        </div>
        <StatusBadge status={data.status} />
      </div>

      <section className="mt-8 space-y-4">
        {data.messages.length === 0 && <p className="text-neutral-500">No messages yet.</p>}
        {data.messages.map((m) => (
          <div key={m.id} className="rounded-lg border border-neutral-200 dark:border-neutral-800 p-4">
            <div className="flex justify-between text-xs text-neutral-500">
              <span className="font-medium">{m.author_display} ({m.author_type})</span>
              <span>{new Date(m.created_at).toLocaleString()}</span>
            </div>
            <p className="mt-2 whitespace-pre-wrap text-sm">{m.body}</p>
          </div>
        ))}
      </section>

      <section className="mt-8">
        <h2 className="text-sm font-semibold">Add a reply</h2>
        <Textarea rows={4} className="mt-2" value={reply} onChange={(e) => setReply(e.target.value)} />
        <Button className="mt-3" disabled={!reply.trim() || sendReply.isPending} onClick={() => sendReply.mutate()}>
          {sendReply.isPending ? "Sending..." : "Send reply"}
        </Button>
      </section>

      <section className="mt-10">
        <h2 className="text-sm font-semibold">Timeline</h2>
        <ol className="mt-3 space-y-2 border-l border-neutral-200 dark:border-neutral-800 pl-4">
          {data.timeline.map((e, i) => (
            <li key={i} className="text-sm">
              <span className="text-neutral-500">{new Date(e.created_at).toLocaleString()}: </span>
              {STATUS_LABEL[e.to_status] ?? e.to_status}{e.note ? ` — ${e.note}` : ""}
            </li>
          ))}
        </ol>
      </section>
    </main>
  );
}

function Skeleton() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-16 animate-pulse">
      <div className="h-4 w-40 rounded bg-neutral-200 dark:bg-neutral-800" />
      <div className="mt-3 h-8 w-2/3 rounded bg-neutral-200 dark:bg-neutral-800" />
      <div className="mt-8 space-y-4">{[0,1,2].map(i => <div key={i} className="h-24 rounded-lg bg-neutral-200 dark:bg-neutral-800" />)}</div>
    </main>
  );
}
