"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { toast } from "sonner";
import { clientApi, setClientToken } from "@/lib/api";
import { Button, Input } from "@/components/ui/primitives";

const reqSchema = z.object({ case_number: z.string().min(3), email: z.string().email() });
const otpSchema = z.object({ code: z.string().min(4).max(10) });

export default function Track() {
  const [stage, setStage] = useState<"request" | "verify">("request");
  const [ctx, setCtx] = useState<{ case_number: string; email: string }>({ case_number: "", email: "" });
  const router = useRouter();

  const reqForm = useForm({ resolver: zodResolver(reqSchema) });
  const otpForm = useForm({ resolver: zodResolver(otpSchema) });

  async function requestOtp(data: z.infer<typeof reqSchema>) {
    try {
      await clientApi("/support/tickets/otp", { method: "POST", body: JSON.stringify(data) });
      setCtx(data); setStage("verify");
      toast.success("If the case and email match, a code has been sent.");
    } catch (e) { toast.error((e as Error).message); }
  }

  async function verifyOtp(data: z.infer<typeof otpSchema>) {
    try {
      const res = await clientApi<{ access_token: string }>("/support/tickets/otp/verify", {
        method: "POST", body: JSON.stringify({ ...ctx, code: data.code }),
      });
      setClientToken(res.access_token);
      router.push(`/support/case/${encodeURIComponent(ctx.case_number)}`);
    } catch (e) { toast.error((e as Error).message); }
  }

  return (
    <main className="mx-auto max-w-md px-6 py-20">
      <h1 className="text-3xl font-semibold">Track your request</h1>
      {stage === "request" ? (
        <form className="mt-8 grid gap-4" onSubmit={reqForm.handleSubmit(requestOtp)}>
          <label className="block"><span className="mb-1.5 block text-sm font-medium">Case Number</span>
            <Input aria-label="Case Number" placeholder="SUP-2026-XXXXXXXXXX" {...reqForm.register("case_number")} /></label>
          <label className="block"><span className="mb-1.5 block text-sm font-medium">Email</span>
            <Input aria-label="Email" type="email" {...reqForm.register("email")} /></label>
          <Button type="submit">Request code</Button>
          <p className="text-xs text-neutral-500">Your case number alone can never open a ticket. We email a one-time code to verify it is you.</p>
        </form>
      ) : (
        <form className="mt-8 grid gap-4" onSubmit={otpForm.handleSubmit(verifyOtp)}>
          <p className="text-sm text-neutral-600 dark:text-neutral-400">Enter the verification code sent to {ctx.email}.</p>
          <Input aria-label="Code" inputMode="numeric" placeholder="6-digit code" {...otpForm.register("code")} />
          <Button type="submit">Verify</Button>
          <button type="button" className="text-xs text-neutral-500 underline" onClick={() => setStage("request")}>Use a different case number</button>
        </form>
      )}
    </main>
  );
}
