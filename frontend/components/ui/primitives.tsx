"use client";
import { cn } from "@/lib/utils";
import { forwardRef, type ButtonHTMLAttributes, type InputHTMLAttributes,
  type TextareaHTMLAttributes } from "react";

export const Button = forwardRef<HTMLButtonElement, ButtonHTMLAttributes<HTMLButtonElement> & { variant?: "primary" | "ghost" | "danger" }>(
  ({ className, variant = "primary", ...props }, ref) => (
    <button ref={ref} className={cn(
      "inline-flex items-center justify-center rounded-md px-4 py-2 text-sm font-medium transition-colors disabled:opacity-50 disabled:pointer-events-none",
      variant === "primary" && "bg-brand text-brand-fg hover:opacity-90",
      variant === "ghost" && "hover:bg-neutral-200 dark:hover:bg-neutral-800",
      variant === "danger" && "bg-red-600 text-white hover:bg-red-700",
      className,
    )} {...props} />
  ),
);
Button.displayName = "Button";

export const Input = forwardRef<HTMLInputElement, InputHTMLAttributes<HTMLInputElement>>(
  ({ className, ...props }, ref) => (
    <input ref={ref} className={cn(
      "w-full rounded-md border border-neutral-300 dark:border-neutral-700 bg-transparent px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand/40",
      className,
    )} {...props} />
  ),
);
Input.displayName = "Input";

export const Textarea = forwardRef<HTMLTextAreaElement, TextareaHTMLAttributes<HTMLTextAreaElement>>(
  ({ className, ...props }, ref) => (
    <textarea ref={ref} className={cn(
      "w-full rounded-md border border-neutral-300 dark:border-neutral-700 bg-transparent px-3 py-2 text-sm outline-none focus:ring-2 focus:ring-brand/40",
      className,
    )} {...props} />
  ),
);
Textarea.displayName = "Textarea";

export function StatusBadge({ status }: { status: string }) {
  const tone: Record<string, string> = {
    new: "bg-blue-100 text-blue-800", open: "bg-indigo-100 text-indigo-800",
    in_progress: "bg-amber-100 text-amber-800", pending_client: "bg-purple-100 text-purple-800",
    resolved: "bg-green-100 text-green-800", closed: "bg-neutral-200 text-neutral-700",
  };
  return <span className={cn("rounded-full px-2.5 py-0.5 text-xs font-medium", tone[status] ?? "bg-neutral-100 text-neutral-700")}>{status}</span>;
}
