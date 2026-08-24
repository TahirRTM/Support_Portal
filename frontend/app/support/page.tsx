import Link from "next/link";
import { Button } from "@/components/ui/primitives";

export default function SupportHome() {
  return (
    <main className="mx-auto max-w-3xl px-6 py-20">
      <p className="text-sm font-medium uppercase tracking-widest text-brand">Support</p>
      <h1 className="mt-3 text-4xl font-semibold leading-tight">How can we help?</h1>
      <p className="mt-4 max-w-prose text-neutral-600 dark:text-neutral-400">
        Open a support request and track its progress anytime with your case number
        and email. No account required.
      </p>
      <div className="mt-8 flex gap-3">
        <Link href="/support/create"><Button>Create a request</Button></Link>
        <Link href="/support/track"><Button variant="ghost">Track a request</Button></Link>
      </div>
    </main>
  );
}
