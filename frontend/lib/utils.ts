import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";
export function cn(...inputs: ClassValue[]) { return twMerge(clsx(inputs)); }

export const STATUS_LABEL: Record<string, string> = {
  new: "New", open: "Open", in_progress: "In Progress",
  pending_client: "Pending Client", pending_internal: "Pending Internal",
  resolved: "Resolved", closed: "Closed", reopened: "Reopened",
};
