// Call Session Types
export interface CallSession {
  id: number;
  call_sid: string | null;
  agent_name: string;
  customer_name: string;
  customer_phone: string;
  status: "active" | "ended";
  started_at: string;
  ended_at: string | null;
  created_at: string;
}

export interface TranscriptChunk {
  id: number;
  session_id: number;
  speaker: "agent" | "customer";
  text: string;
  timestamp: string;
  created_at: string;
}

export interface AISuggestion {
  id: number;
  session_id: number;
  chunk_id: number;
  suggested_response: string;
  objection_label: string;
  compliance_warning: string | null;
  call_stage: string;
  created_at: string;
}

export interface ComplianceFlag {
  id: number;
  session_id: number;
  chunk_id: number;
  detection_method: "rule_based" | "ai_assisted";
  trigger_phrase: string | null;
  warning_message: string;
  severity: "high" | "medium" | "low";
  created_at: string;
}

export interface ObjectionEvent {
  id: number;
  session_id: number;
  chunk_id: number;
  objection_label: string;
  detection_method: "rule_based" | "ai_assisted";
  source_text: string;
  created_at: string;
}

export interface PostCallSummary {
  overall_summary: string;
  main_concerns: string[];
  objections_raised: string[];
  compliance_warnings: string[];
  suggested_next_action: string;
}

// API Response Types
export interface StartCallRequest {
  agent_name: string;
  customer_name: string;
  customer_phone: string;
  call_sid?: string;
}

export interface CallSessionResponse extends CallSession {}

export interface CallListResponse {
  total: number;
  sessions: CallSessionResponse[];
}

export interface TranscriptUpdate {
  event: string;
  session_id: number;
  transcript: {
    id: number;
    speaker: string;
    text: string;
    timestamp: string;
  };
  ai_suggestion: {
    id: number;
    suggested_response: string;
    objection_label: string;
    compliance_warning: string | null;
    call_stage: string;
  };
  objection_detected: boolean;
  objection_label: string;
  compliance_alert: string | null;
}

export interface EndCallResponse {
  message: string;
  session_id: number;
  status: string;
  ended_at: string;
  summary: PostCallSummary;
}

// CRM Types
export interface CRMContact {
  contact_found: boolean;
  contact_id: string | null;
  full_name: string | null;
  first_name: string | null;
  last_name: string | null;
  phone: string | null;
  email: string | null;
  tags: string[];
  notes_summary: string | null;
  custom_fields: Record<string, unknown>;
  pipeline_stage: string | null;
  opportunities: string[];
  source: string;
}

export interface CRMStatus {
  enabled: boolean;
  provider: string;
  configured: boolean;
  token_present: boolean;
}

// RAG Types
export interface RAGStatus {
  enabled: boolean;
  vector_store_exists: boolean;
  indexed_file_count: number;
  total_chunks: number;
}

export interface IngestResponse {
  success: boolean;
  message: string;
  files_processed: number;
  total_chunks: number;
}

// Dashboard Types
export interface DashboardStats {
  active_calls: number;
  total_sessions_today: number;
  objections_flagged_today: number;
  compliance_alerts_today: number;
  avg_response_time: string;
  sessions_this_week: number;
  objections_this_week: number;
  compliance_this_week: number;
}

// Live Call State
export interface LiveCallState {
  session: CallSession | null;
  transcript: TranscriptChunk[];
  suggestions: AISuggestion[];
  compliance_flags: ComplianceFlag[];
  objection_events: ObjectionEvent[];
  crm_contact: CRMContact | null;
  isConnected: boolean;
  isLoading: boolean;
  error: string | null;
}

// Call Stage
export type CallStage =
  | "opening"
  | "discovery"
  | "qualification"
  | "pitch"
  | "objection_handling"
  | "closing"
  | "unknown";

// Objection Label
export type ObjectionLabel =
  | "price"
  | "not_interested"
  | "needs_time"
  | "already_have_solution"
  | "hesitant"
  | "none";

// User
export interface User {
  id: string;
  name: string;
  email: string;
  role: "agent" | "admin" | "manager";
  avatar?: string;
}