import { 
  CallSession, 
  CallSessionResponse, 
  CallListResponse,
  TranscriptChunk,
  AISuggestion,
  ComplianceFlag,
  ObjectionEvent,
  PostCallSummary,
  StartCallRequest,
  CRMContact,
  CRMStatus,
  RAGStatus,
  DashboardStats 
} from "@/lib/types";

const BACKEND_URL = process.env.NEXT_PUBLIC_BACKEND_URL || "http://localhost:8000";
const API_PREFIX = "/api/v1";

class ApiError extends Error {
  constructor(public status: number, message: string) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  endpoint: string,
  options: RequestInit = {}
): Promise<T> {
  const url = `${BACKEND_URL}${endpoint}`;
  
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        "Content-Type": "application/json",
        ...options.headers,
      },
    });

    if (!response.ok) {
      const error = await response.text().catch(() => "Unknown error");
      throw new ApiError(response.status, error);
    }

    if (response.status === 204) {
      return null as any;
    }

    const text = await response.text();
    return (text ? JSON.parse(text) : null) as T;
  } catch (error) {
    if (error instanceof ApiError) throw error;
    throw new ApiError(0, `Network error: ${(error as Error).message}`);
  }
}

// Health
export async function getHealth(): Promise<{ status: string }> {
  return request("/health");
}

// Calls
export async function startCall(data: StartCallRequest): Promise<CallSessionResponse> {
  return request(`${API_PREFIX}/calls/start`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getCalls(skip = 0, limit = 50): Promise<CallListResponse> {
  return request(`${API_PREFIX}/calls?skip=${skip}&limit=${limit}`);
}

export async function getCall(sessionId: number): Promise<CallSessionResponse> {
  return request(`${API_PREFIX}/calls/${sessionId}`);
}

export async function endCall(sessionId: number): Promise<{
  message: string;
  session_id: number;
  status: string;
  ended_at: string;
  summary: PostCallSummary;
}> {
  return request(`${API_PREFIX}/calls/${sessionId}/end`, {
    method: "POST",
  });
}

export async function deleteCall(sessionId: number): Promise<void> {
  return request(`${API_PREFIX}/calls/${sessionId}`, {
    method: "DELETE",
  });
}

// Transcripts
export async function sendTranscript(data: {
  session_id: number;
  speaker: "agent" | "customer";
  text: string;
  timestamp: string;
}): Promise<{ id: number }> {
  return request(`${API_PREFIX}/transcripts`, {
    method: "POST",
    body: JSON.stringify(data),
  });
}

export async function getTranscripts(sessionId: number): Promise<TranscriptChunk[]> {
  const response = await request<{session_id: number; total: number; chunks: TranscriptChunk[]}>(`${API_PREFIX}/calls/${sessionId}/transcripts`);
  return response.chunks;
}

// Suggestions
export async function getSuggestions(sessionId: number): Promise<AISuggestion[]> {
  const response = await request<{session_id: number; total: number; suggestions: AISuggestion[]}>(`${API_PREFIX}/calls/${sessionId}/suggestions`);
  return response.suggestions;
}

// CRM
export async function getCRMStatus(): Promise<CRMStatus> {
  return request(`${API_PREFIX}/crm/status`);
}

export async function lookupContactByPhone(phone: string): Promise<CRMContact> {
  return request(`${API_PREFIX}/crm/contact/by-phone?phone=${encodeURIComponent(phone)}`);
}

export async function lookupContactByEmail(email: string): Promise<CRMContact> {
  return request(`${API_PREFIX}/crm/contact/by-email?email=${encodeURIComponent(email)}`);
}

// RAG
export async function getRAGStatus(): Promise<RAGStatus> {
  return request(`${API_PREFIX}/rag/status`);
}

export async function triggerIngest(): Promise<{
  success: boolean;
  message: string;
  files_processed: number;
  total_chunks: number;
}> {
  return request(`${API_PREFIX}/rag/ingest`, {
    method: "POST",
  });
}

// Dashboard Stats (mock implementation)
export async function getSettings(): Promise<{ settings: Record<string, string> }> {
  return request(`${API_PREFIX}/settings`);
}

export async function updateSettings(settings: Record<string, string>): Promise<{ settings: Record<string, string> }> {
  return request(`${API_PREFIX}/settings`, {
    method: "POST",
    body: JSON.stringify({ settings }),
  });
}

export async function getDashboardStats(): Promise<DashboardStats> {
  try {
    const calls = await getCalls(0, 100);
    const today = new Date().toDateString();
    const sessionsToday = calls.sessions.filter((s) => {
      // Append 'Z' to treat sqlite naive timestamp as UTC
      const dateStr = s.started_at.endsWith('Z') ? s.started_at : `${s.started_at}Z`;
      return new Date(dateStr).toDateString() === today;
    });
    
    return {
      active_calls: sessionsToday.filter((s) => s.status === "active").length,
      total_sessions_today: sessionsToday.length,
      objections_flagged_today: 0, // Would need to aggregate from DB
      compliance_alerts_today: 0,
      avg_response_time: "1.2s",
      sessions_this_week: calls.total,
      objections_this_week: 0,
      compliance_this_week: 0,
    };
  } catch {
    return {
      active_calls: 0,
      total_sessions_today: 0,
      objections_flagged_today: 0,
      compliance_alerts_today: 0,
      avg_response_time: "0s",
      sessions_this_week: 0,
      objections_this_week: 0,
      compliance_this_week: 0,
    };
  }
}
export { ApiError, BACKEND_URL };