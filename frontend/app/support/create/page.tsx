"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useMutation, useQuery } from "@tanstack/react-query";
import { toast } from "sonner";
import { useState } from "react";
import { api } from "@/lib/api";
import type { Option, TicketCreated } from "@/types";
import { Button, Input, Textarea } from "@/components/ui/primitives";

const schema = z.object({
  name: z.string().min(1, "Required"),
  company: z.string().optional(),
  email: z.string().email(),
  phone: z.string().optional(),
  subject: z.string().min(3),
  description: z.string().min(3),
  category_id: z.string().uuid().optional().or(z.literal("")),
  priority_id: z.string().uuid().optional().or(z.literal("")),
});
type FormData = z.infer<typeof schema>;

export default function CreateTicket() {
  const [created, setCreated] = useState<TicketCreated | null>(null);
  const cats = useQuery({ queryKey: ["categories"], queryFn: () => api<Option[]>("/reference/categories") });
  const prios = useQuery({ queryKey: ["priorities"], queryFn: () => api<Option[]>("/reference/priorities") });
  const { register, handleSubmit, formState: { errors, isSubmitting } } =
    useForm<FormData>({ resolver: zodResolver(schema) });

  const mutation = useMutation({
    mutationFn: (data: FormData) =>
      api<TicketCreated>("/support/tickets", {
        method: "POST",
        body: JSON.stringify({
          ...data,
          category_id: data.category_id || null,
          priority_id: data.priority_id || null,
          // In production a real Turnstile token is attached here.
          captcha_token: process.env.NEXT_PUBLIC_TURNSTILE_SITE_KEY ? undefined : "dev-bypass",
        }),
      }),
    onSuccess: (d) => { setCreated(d); toast.success("Support Request Received"); },
    onError: (e: Error) => toast.error(e.message),
  });

  if (created) {
    return (
      <main className="mx-auto max-w-xl px-6 py-20">
        <h1 className="text-3xl font-semibold">Support Request Received</h1>
        <p className="mt-3 text-neutral-600 dark:text-neutral-400">
          Keep your case number safe. You will need it plus your email to track this request.
        </p>
        <div className="mt-6 rounded-lg border border-neutral-200 dark:border-neutral-800 p-5">
          <div className="text-xs uppercase tracking-wide text-neutral-500">Case Number</div>
          <div data-testid="case-number" className="mt-1 font-mono text-2xl">{created.case_number}</div>
          <div className="mt-3 text-sm text-neutral-500">Created {new Date(created.created_at).toLocaleString()}</div>
        </div>
        <p className="mt-6 text-sm">A confirmation email is on its way. Track anytime at <a className="text-brand underline" href="/support/track">/support/track</a>.</p>
      </main>
    );
  }

  return (
    <main className="mx-auto max-w-2xl px-6 py-16">
      <h1 className="text-3xl font-semibold">Create a support request</h1>
      <form className="mt-8 grid gap-5" onSubmit={handleSubmit((d) => mutation.mutate(d))}>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Name" error={errors.name?.message}><Input aria-label="Name" {...register("name")} /></Field>
          <Field label="Company"><Input aria-label="Company" {...register("company")} /></Field>
          <Field label="Email" error={errors.email?.message}><Input aria-label="Email" type="email" {...register("email")} /></Field>
          <Field label="Phone"><Input aria-label="Phone" {...register("phone")} /></Field>
        </div>
        <Field label="Subject" error={errors.subject?.message}><Input aria-label="Subject" {...register("subject")} /></Field>
        <div className="grid gap-4 sm:grid-cols-2">
          <Field label="Category">
            <select className="w-full rounded-md border border-neutral-300 dark:border-neutral-700 bg-transparent px-3 py-2 text-sm" {...register("category_id")}>
              <option value="">Auto-detect</option>
              {cats.data?.map((c) => <option key={c.id} value={c.id}>{c.name}</option>)}
            </select>
          </Field>
          <Field label="Priority">
            <select className="w-full rounded-md border border-neutral-300 dark:border-neutral-700 bg-transparent px-3 py-2 text-sm" {...register("priority_id")}>
              <option value="">Auto-detect</option>
              {prios.data?.map((p) => <option key={p.id} value={p.id}>{p.name}</option>)}
            </select>
          </Field>
        </div>
        <Field label="Description" error={errors.description?.message}>
          <Textarea aria-label="Description" rows={6} {...register("description")} />
        </Field>
        <Button type="submit" disabled={isSubmitting || mutation.isPending}>
          {mutation.isPending ? "Submitting..." : "Submit request"}
        </Button>
      </form>
    </main>
  );
}

function Field({ label, error, children }: { label: string; error?: string; children: React.ReactNode }) {
  return (
    <label className="block">
      <span className="mb-1.5 block text-sm font-medium">{label}</span>
      {children}
      {error && <span className="mt-1 block text-xs text-red-600">{error}</span>}
    </label>
  );
}
