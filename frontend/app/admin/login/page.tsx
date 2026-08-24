"use client";
import { useForm } from "react-hook-form";
import { zodResolver } from "@hookform/resolvers/zod";
import { z } from "zod";
import { useRouter } from "next/navigation";
import { toast } from "sonner";
import { api, setAccessToken } from "@/lib/api";
import { Button, Input } from "@/components/ui/primitives";

const schema = z.object({ email: z.string().email(), password: z.string().min(1) });

export default function AdminLogin() {
  const router = useRouter();
  const { register, handleSubmit, formState: { errors, isSubmitting } } =
    useForm({ resolver: zodResolver(schema) });

  async function onSubmit(data: z.infer<typeof schema>) {
    try {
      const res = await api<{ access_token: string }>("/auth/login", {
        method: "POST", body: JSON.stringify(data),
      });
      setAccessToken(res.access_token);
      router.push("/admin");
    } catch (e) { toast.error((e as Error).message); }
  }

  return (
    <main className="grid min-h-screen place-items-center px-6">
      <form onSubmit={handleSubmit(onSubmit)} className="w-full max-w-sm rounded-xl border border-neutral-200 dark:border-neutral-800 p-8">
        <h1 className="text-2xl font-semibold">Support Console</h1>
        <p className="mt-1 text-sm text-neutral-500">Sign in to manage tickets.</p>
        <label className="mt-6 block"><span className="mb-1.5 block text-sm font-medium">Email</span>
          <Input type="email" {...register("email")} />
          {errors.email && <span className="text-xs text-red-600">{errors.email.message}</span>}</label>
        <label className="mt-4 block"><span className="mb-1.5 block text-sm font-medium">Password</span>
          <Input type="password" {...register("password")} /></label>
        <Button className="mt-6 w-full" type="submit" disabled={isSubmitting}>
          {isSubmitting ? "Signing in..." : "Sign in"}
        </Button>
      </form>
    </main>
  );
}
