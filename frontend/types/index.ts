export type TicketStatus =
  | "new" | "open" | "in_progress" | "pending_client"
  | "pending_internal" | "resolved" | "closed" | "reopened";

export interface Option { id: string; name: string; }

export interface TicketCreated {
  case_number: string;
  status: TicketStatus;
  created_at: string;
  message: string;
  acknowledgment: string | null;
}

export interface PublicMessage {
  id: string; author_type: string; author_display: string;
  body: string; created_at: string;
}

export interface StatusEvent {
  from_status: string | null; to_status: string; created_at: string; note: string | null;
}

export interface ClientTicketView {
  case_number: string; subject: string; status: TicketStatus;
  created_at: string; updated_at: string;
  messages: PublicMessage[]; timeline: StatusEvent[];
  attachments: { id: string; original_filename: string; content_type: string; size_bytes: number }[];
}

export interface Page<T> { items: T[]; total: number; page: number; page_size: number; }
export interface AdminTicketRow {
  id: string; case_number: string; subject: string; status: TicketStatus;
  client_name: string; client_email: string; created_at: string; updated_at: string;
  sla_response_breached: boolean; sla_resolution_breached: boolean;
  assigned_agent_id: string | null;
}
