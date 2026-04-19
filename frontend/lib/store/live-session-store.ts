import { create } from "zustand";
import { 
  CallSession, 
  TranscriptChunk, 
  AISuggestion, 
  CRMContact,
  TranscriptUpdate 
} from "@/lib/types";

interface LiveSessionState {
  // Session
  session: CallSession | null;
  setSession: (session: CallSession | null) => void;
  
  // Transcript
  transcript: TranscriptChunk[];
  addTranscript: (chunk: TranscriptChunk) => void;
  setTranscript: (transcript: TranscriptChunk[]) => void;
  
  // Suggestions
  suggestions: AISuggestion[];
  addSuggestion: (suggestion: AISuggestion) => void;
  setSuggestions: (suggestions: AISuggestion[]) => void;
  
  // CRM
  crmContact: CRMContact | null;
  setCRMContact: (contact: CRMContact | null) => void;
  
  // Connection state
  isConnected: boolean;
  setConnected: (connected: boolean) => void;
  
  // Error state
  error: string | null;
  setError: (error: string | null) => void;
  
  // Loading state
  isLoading: boolean;
  setLoading: (loading: boolean) => void;
  
  // Reset
  reset: () => void;
}

export const useLiveSessionStore = create<LiveSessionState>((set) => ({
  session: null,
  setSession: (session) => set({ session }),
  
  transcript: [],
  addTranscript: (chunk) => set((state) => ({ 
    transcript: [...state.transcript, chunk] 
  })),
  setTranscript: (transcript) => set({ transcript }),
  
  suggestions: [],
  addSuggestion: (suggestion) => set((state) => ({ 
    suggestions: [...state.suggestions, suggestion] 
  })),
  setSuggestions: (suggestions) => set({ suggestions }),
  
  crmContact: null,
  setCRMContact: (crmContact) => set({ crmContact }),
  
  isConnected: false,
  setConnected: (isConnected) => set({ isConnected }),
  
  error: null,
  setError: (error) => set({ error }),
  
  isLoading: false,
  setLoading: (isLoading) => set({ isLoading }),
  
  reset: () => set({
    session: null,
    transcript: [],
    suggestions: [],
    crmContact: null,
    isConnected: false,
    error: null,
    isLoading: false,
  }),
}));

// Handle WebSocket updates
export function handleWsUpdate(update: TranscriptUpdate) {
  const store = useLiveSessionStore.getState();
  
  if (update.transcript) {
    store.addTranscript({
      id: update.transcript.id,
      session_id: update.session_id,
      speaker: update.transcript.speaker as "agent" | "customer",
      text: update.transcript.text,
      timestamp: update.transcript.timestamp,
      created_at: update.transcript.timestamp,
    });
  }
  
  if (update.ai_suggestion) {
    store.addSuggestion({
      id: update.ai_suggestion.id,
      session_id: update.session_id,
      chunk_id: update.transcript.id,
      suggested_response: update.ai_suggestion.suggested_response,
      objection_label: update.ai_suggestion.objection_label,
      compliance_warning: update.ai_suggestion.compliance_warning,
      call_stage: update.ai_suggestion.call_stage,
      created_at: new Date().toISOString(),
    });
  }
}