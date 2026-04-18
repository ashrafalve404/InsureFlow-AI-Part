"use client";

import { useEffect, useState, useRef } from "react";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { 
  getCall, 
  getTranscripts, 
  getSuggestions, 
  lookupContactByPhone, 
  startCall, 
  sendTranscript 
} from "@/lib/api";
import { useLiveSessionStore, handleWsUpdate } from "@/lib/store/live-session-store";
import { wsManager } from "@/lib/services/ws";
import { cn, formatTime, generateInitials } from "@/lib/utils";
import { CallSession, TranscriptChunk, AISuggestion, CRMContact } from "@/lib/types";
import { 
  Phone, 
  User, 
  AlertTriangle, 
  Shield,
  MessageSquare,
  Send,
  Clock,
  Tag,
  Building,
  FileText,
  ChevronDown,
  ChevronUp,
  Menu
} from "lucide-react";

function LiveCallContent() {
  const searchParams = useSearchParams();
  const sessionIdFromUrl = searchParams.get("id");
  const initialSessionId = sessionIdFromUrl ? parseInt(sessionIdFromUrl) : null;
  
  const { 
    session, setSession, 
    transcript: transcripts, setTranscript,
    suggestions, setSuggestions,
    crmContact, setCRMContact,
    isConnected, setConnected,
    reset
  } = useLiveSessionStore();

  const [sessionId, setSessionId] = useState<number | null>(initialSessionId);
  const [loading, setLoading] = useState(!!initialSessionId);
  const [manualInput, setManualInput] = useState("");
  const [activePanel, setActivePanel] = useState<"transcript" | "ai" | "crm">("transcript");
  const messagesEndRef = useRef<HTMLDivElement>(null);

  const scrollToBottom = () => {
    messagesEndRef.current?.scrollIntoView({ behavior: "smooth" });
  };

  // Sync session ID with URL
  useEffect(() => {
    if (initialSessionId !== sessionId) {
      setSessionId(initialSessionId);
    }
  }, [initialSessionId]);

  // Auto-scroll when transcripts update
  useEffect(() => {
    scrollToBottom();
  }, [transcripts]);

  // Handle WebSocket connection and subscriptions
  useEffect(() => {
    if (!sessionId) return;

    const connectAndSubscribe = async () => {
      try {
        await wsManager.connect(sessionId);
        setConnected(true);
      } catch (err) {
        console.error("WS Connection failed:", err);
      }
    };

    connectAndSubscribe();
    const unsubscribe = wsManager.subscribe(handleWsUpdate);

    return () => {
      unsubscribe();
      wsManager.disconnect();
      setConnected(false);
    };
  }, [sessionId, setConnected]);

  // Initial data fetch
  useEffect(() => {
    if (!sessionId) {
      setLoading(false);
      return;
    }
    
    async function fetchData() {
      setLoading(true);
      try {
        const sessionNum = sessionId as number;
        const [sessionData, transcriptData, suggestionData] = await Promise.all([
          getCall(sessionNum),
          getTranscripts(sessionNum),
          getSuggestions(sessionNum),
        ]);
        
        setSession(sessionData);
        setTranscript(transcriptData);
        setSuggestions(suggestionData);
        
        if (sessionData.customer_phone) {
          try {
            const crm = await lookupContactByPhone(sessionData.customer_phone);
            if (crm.contact_found) {
              setCRMContact(crm);
            }
          } catch (e) {
            console.log("No CRM contact found");
          }
        }
      } catch (error) {
        console.error("Failed to fetch session data:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [sessionId, setSession, setTranscript, setSuggestions, setCRMContact]);

  const latestSuggestion = suggestions && suggestions.length > 0 ? suggestions[suggestions.length - 1] : null;
  const callStage = latestSuggestion?.call_stage || "unknown";

  const handleManualSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualInput.trim() || !sessionId) return;
    
    const text = manualInput;
    setManualInput("");

    try {
      // For testing, we alternate speakers or just use agent
      // In a real scenario, this would come from a telephony stream
      const speaker = transcripts.length % 2 === 0 ? "agent" : "customer";
      
      await sendTranscript({
        session_id: sessionId,
        speaker: speaker,
        text: text,
        timestamp: new Date().toISOString(),
      });
    } catch (err) {
      console.error("Failed to send transcript:", err);
    }
  };

  const pathname = "/dashboard/live";

  const togglePanel = (panel: "transcript" | "ai" | "crm") => {
    if (typeof window !== "undefined" && window.innerWidth < 1024) {
      setActivePanel(activePanel === panel ? "transcript" : panel);
    }
  };

  return (
    <DashboardLayout pathname={pathname}>
      <div className="flex flex-col lg:flex-row h-full -m-4 lg:m-0">
        {/* Mobile Panel Tabs */}
        <div className="flex lg:hidden border-b border-border bg-card">
          <button
            onClick={() => togglePanel("transcript")}
            className={cn(
              "flex-1 py-3 px-4 text-sm font-medium flex items-center justify-center gap-2",
              activePanel === "transcript" ? "text-primary border-b-2 border-primary" : "text-muted-foreground"
            )}
          >
            <Phone className="w-4 h-4" /> Transcript
          </button>
          <button
            onClick={() => togglePanel("ai")}
            className={cn(
              "flex-1 py-3 px-4 text-sm font-medium flex items-center justify-center gap-2",
              activePanel === "ai" ? "text-primary border-b-2 border-primary" : "text-muted-foreground"
            )}
          >
            <MessageSquare className="w-4 h-4" /> AI
          </button>
          <button
            onClick={() => togglePanel("crm")}
            className={cn(
              "flex-1 py-3 px-4 text-sm font-medium flex items-center justify-center gap-2",
              activePanel === "crm" ? "text-primary border-b-2 border-primary" : "text-muted-foreground"
            )}
          >
            <User className="w-4 h-4" /> CRM
          </button>
        </div>

        {/* Left Panel - Transcript */}
        <div className={cn(
          "w-full lg:w-1/3 border-r border-border flex flex-col",
          "lg:flex",
          (activePanel === "transcript" || typeof window === "undefined") ? "flex" : "hidden"
        )}>
          {/* Session Header */}
          <div className="p-3 lg:p-4 border-b border-border">
            {loading ? (
              <div className="animate-pulse">
                <div className="h-4 bg-muted rounded w-1/3 mb-2"></div>
                <div className="h-3 bg-muted rounded w-1/2"></div>
              </div>
            ) : session ? (
              <>
                <div className="flex items-center gap-2 lg:gap-3">
                  <div className="w-8 lg:w-10 h-8 lg:h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <Phone className="w-4 lg:w-5 h-4 lg:h-5 text-primary" />
                  </div>
                  <div className="min-w-0">
                    <h2 className="font-semibold text-sm lg:text-base truncate">{session.customer_name}</h2>
                    <p className="text-xs lg:text-sm text-muted-foreground">{session.customer_phone}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2 mt-2 lg:mt-3 flex-wrap">
                  <span className={session.status === "active" ? "inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium bg-red-500/10 text-red-500 border border-red-500/20" : "inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium bg-muted"}>
                    {session.status === "active" && <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />}
                    {session.status === "active" ? "Live" : session.status}
                  </span>
                  <span className={cn(
                    "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium",
                    isConnected ? "bg-primary/10 text-primary" : "bg-red-500/10 text-red-500"
                  )}>
                    {isConnected ? "Connected" : "Disconnected"}
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-muted">
                    <Clock className="w-3 h-3" />
                    {callStage}
                  </span>
                </div>
              </>
            ) : (
              <div className="flex flex-col gap-4">
                <div className="text-muted-foreground text-sm">No session selected. Start a call from the dashboard or history.</div>
                <button 
                  onClick={async () => {
                    setLoading(true);
                    try {
                      const newSession = await startCall({
                        agent_name: "Sarah Agent",
                        customer_name: "Test Customer",
                        customer_phone: "+15550199"
                      });
                      window.location.href = `/dashboard/live?id=${newSession.id}`;
                    } catch (e) {
                      console.error(e);
                    } finally {
                      setLoading(false);
                    }
                  }}
                  className="px-4 py-2 rounded-xl bg-primary text-primary-foreground text-sm font-medium"
                >
                  Start New Test Call
                </button>
              </div>
            )}
          </div>

          {/* Transcript Stream */}
          <div className="flex-1 overflow-y-auto p-3 lg:p-4 space-y-3 lg:space-y-4">
            {loading ? (
              <div className="text-center py-8 text-muted-foreground">Loading...</div>
            ) : !transcripts || transcripts.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">No transcripts yet. Use the input below to simulate conversation.</div>
            ) : (
              <>
                {transcripts.map((chunk, i) => (
                  <div
                    key={`${chunk.id}-${i}`}
                    className={cn(
                      "flex flex-col animate-in fade-in slide-in-from-bottom-2 duration-300",
                      chunk.speaker === "agent" ? "items-end" : "items-start"
                    )}
                  >
                    <div className="flex items-center gap-2 mb-1">
                      <span className={cn(
                        "text-xs font-medium",
                        chunk.speaker === "agent" ? "text-primary" : "text-muted-foreground"
                      )}>
                        {chunk.speaker === "agent" ? "You" : (session?.customer_name || "Customer")}
                      </span>
                      <span className="text-xs text-muted-foreground">
                        {formatTime(chunk.timestamp)}
                      </span>
                    </div>
                    <div className={cn(
                      "max-w-[85%] px-3 lg:px-4 py-2 lg:py-3 rounded-xl lg:rounded-2xl text-sm shadow-sm",
                      chunk.speaker === "agent"
                        ? "bg-primary text-primary-foreground rounded-br-md"
                        : "bg-muted rounded-bl-md"
                    )}>
                      {chunk.text}
                    </div>
                  </div>
                ))}
                <div ref={messagesEndRef} />
              </>
            )}
          </div>

          {/* Manual Input */}
          <form onSubmit={handleManualSubmit} className="p-3 lg:p-4 border-t border-border">
            <div className="flex gap-2">
              <input
                type="text"
                value={manualInput}
                onChange={(e) => setManualInput(e.target.value)}
                placeholder={session ? "Type to simulate conversation..." : "Select a session first"}
                disabled={!session}
                className="flex-1 px-3 lg:px-4 py-2 rounded-xl border border-border bg-background text-sm focus:outline-none focus:ring-2 focus:ring-primary/20"
              />
              <button 
                type="submit"
                disabled={!session || !manualInput.trim()}
                className="px-3 lg:px-4 py-2 rounded-xl bg-primary text-primary-foreground disabled:opacity-50 disabled:cursor-not-allowed transition-all active:scale-95"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
            <p className="text-[10px] text-muted-foreground mt-2 text-center">
              TIP: Alternate messages to see Agent (You) vs Customer responses.
            </p>
          </form>
        </div>

        {/* Center Panel - AI Suggestions */}
        <div className={cn(
          "w-full lg:w-1/3 border-r border-border flex flex-col",
          "lg:flex",
          activePanel === "ai" ? "flex" : "hidden lg:flex"
        )}>
          <div className="p-3 lg:p-4 border-b border-border">
            <h3 className="font-semibold flex items-center gap-2 text-sm lg:text-base">
              <MessageSquare className="w-4 h-4 text-primary" />
              AI Assistant
            </h3>
          </div>

          <div className="flex-1 overflow-y-auto p-3 lg:p-4">
            {latestSuggestion ? (
              <div className="space-y-3 lg:space-y-4 animate-in fade-in zoom-in-95 duration-300">
                {/* Current Suggestion */}
                <div className="p-3 lg:p-4 rounded-xl lg:rounded-2xl bg-gradient-to-br from-primary/10 via-primary/5 to-background border border-primary/20 shadow-sm relative overflow-hidden">
                  <div className="absolute top-0 right-0 p-2">
                    <div className="w-2 h-2 rounded-full bg-primary animate-pulse" />
                  </div>
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-[10px] uppercase tracking-wider font-bold text-primary">Live Advice</span>
                    <span className="text-[10px] text-muted-foreground">
                      {formatTime(latestSuggestion.created_at)}
                    </span>
                  </div>
                  <p className="text-base lg:text-lg font-semibold leading-tight text-foreground">{latestSuggestion.suggested_response}</p>
                </div>

                {/* Call Stage */}
                <div className="flex items-center justify-between p-2 lg:p-3 rounded-xl bg-muted/50 border border-border/50">
                  <div className="flex items-center gap-2">
                    <Clock className="w-4 h-4 text-muted-foreground" />
                    <span className="text-xs lg:text-sm">Call Stage</span>
                  </div>
                  <span className="text-xs lg:text-sm font-bold uppercase tracking-tight text-primary">{callStage}</span>
                </div>

                {/* Objection */}
                {latestSuggestion.objection_label !== "none" && (
                  <div className="flex items-center gap-3 p-3 lg:p-4 rounded-xl bg-amber-500/10 border border-amber-500/20 animate-bounce-subtle">
                    <div className="p-2 rounded-full bg-amber-500/20">
                      <AlertTriangle className="w-5 h-5 text-amber-600" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-amber-700 uppercase">Objection Detected</p>
                      <p className="text-sm font-medium text-amber-800 capitalize">{latestSuggestion.objection_label}</p>
                    </div>
                  </div>
                )}

                {/* Compliance */}
                {latestSuggestion.compliance_warning && (
                  <div className="flex items-center gap-3 p-3 lg:p-4 rounded-xl bg-red-500/10 border border-red-500/20">
                    <div className="p-2 rounded-full bg-red-500/20">
                      <Shield className="w-5 h-5 text-red-600" />
                    </div>
                    <div>
                      <p className="text-xs font-bold text-red-700 uppercase">Compliance Risk</p>
                      <p className="text-sm font-medium text-red-800">{latestSuggestion.compliance_warning}</p>
                    </div>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-8 lg:py-12 text-center">
                <div className="mb-4 relative inline-block">
                  <MessageSquare className="w-10 lg:w-12 h-10 lg:h-12 mx-auto text-muted-foreground/20" />
                  <div className="absolute inset-0 flex items-center justify-center">
                    <div className="w-2 h-2 rounded-full bg-primary/40 animate-ping" />
                  </div>
                </div>
                <p className="text-sm text-muted-foreground">Subscribed to stream...</p>
                <p className="text-xs text-muted-foreground/60 mt-1">Start speaking to receive AI guidance.</p>
              </div>
            )}
          </div>
        </div>

        {/* Right Panel - CRM & Info */}
        <div className={cn(
          "w-full lg:w-1/3 flex flex-col",
          "lg:flex",
          activePanel === "crm" ? "flex" : "hidden lg:flex"
        )}>
          {/* CRM Contact */}
          <div className="p-3 lg:p-4 border-b border-border">
            <h3 className="font-semibold flex items-center gap-2 mb-3 lg:mb-4 text-sm lg:text-base">
              <User className="w-4 h-4 text-primary" />
              Customer Context
            </h3>
            
            {crmContact ? (
              <div className="space-y-3 lg:space-y-4">
                <div className="flex items-center gap-2 lg:gap-3">
                  <div className="w-10 lg:w-12 h-10 lg:h-12 rounded-full bg-gradient-to-br from-primary to-primary/60 flex items-center justify-center text-sm lg:text-lg font-bold text-white shrink-0 shadow-sm">
                    {generateInitials(crmContact.full_name || "")}
                  </div>
                  <div className="min-w-0">
                    <p className="font-bold text-sm lg:text-base truncate text-foreground">{crmContact.full_name}</p>
                    <p className="text-xs text-muted-foreground truncate">{crmContact.email}</p>
                  </div>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-1">
                  {crmContact.tags.map((tag) => (
                    <span 
                      key={tag}
                      className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-[10px] font-bold uppercase bg-primary/10 text-primary border border-primary/20"
                    >
                      <Tag className="w-2.5 h-2.5" />
                      {tag}
                    </span>
                  ))}
                </div>

                {/* Pipeline Stage */}
                <div className="flex items-center justify-between p-2 lg:p-3 rounded-xl bg-muted/50 border border-border/50">
                  <div className="flex items-center gap-2">
                    <Building className="w-4 h-4 text-muted-foreground" />
                    <span className="text-xs">Pipeline</span>
                  </div>
                  <span className="text-xs font-bold text-foreground">{crmContact.pipeline_stage}</span>
                </div>

                {/* Notes */}
                {crmContact.notes_summary && (
                  <div className="p-2 lg:p-3 rounded-xl bg-primary/5 border border-primary/10">
                    <div className="flex items-center gap-1.5 mb-1.5">
                      <FileText className="w-3.5 h-3.5 text-primary" />
                      <p className="text-[10px] font-bold uppercase text-primary">Past Interaction Summary</p>
                    </div>
                    <p className="text-xs text-muted-foreground leading-relaxed italic">"{crmContact.notes_summary}"</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-6 lg:py-8 text-center bg-muted/30 rounded-xl border border-dashed border-border">
                <User className="w-8 lg:w-10 h-8 lg:h-10 mx-auto text-muted-foreground/30 mb-2" />
                <p className="text-xs text-muted-foreground">Syncing CRM data...</p>
              </div>
            )}
          </div>

          {/* Recent Suggestions History */}
          <div className="flex-1 overflow-y-auto p-3 lg:p-4">
            <h3 className="font-semibold text-xs lg:text-sm mb-3 lg:mb-4 text-muted-foreground uppercase tracking-wider">Previous Insights</h3>
            <div className="space-y-3">
              {suggestions && suggestions.length > 1 ? (
                <>
                  {suggestions.slice(0, -1).reverse().map((suggestion, i) => (
                    <div 
                      key={`${suggestion.id}-${i}`}
                      className="p-3 rounded-xl bg-muted/20 hover:bg-muted/40 border border-transparent hover:border-border transition-all group"
                    >
                      <p className="text-xs lg:text-sm line-clamp-2 text-foreground/80 group-hover:text-foreground">{suggestion.suggested_response}</p>
                      <div className="flex items-center justify-between mt-2">
                        <span className="text-[10px] font-bold text-primary/60 uppercase">{suggestion.call_stage}</span>
                        {suggestion.objection_label !== "none" && (
                          <span className="text-[10px] font-bold text-amber-600 bg-amber-500/10 px-1.5 py-0.5 rounded uppercase">{suggestion.objection_label}</span>
                        )}
                      </div>
                    </div>
                  ))}
                </>
              ) : (
                <div className="flex flex-col items-center justify-center py-10 opacity-30">
                  <div className="w-1 bg-border h-8 mb-2" />
                  <p className="text-[10px] uppercase font-bold text-muted-foreground">Timeline Empty</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}

export default function LiveCallPage() {
  return (
    <Suspense fallback={
      <DashboardLayout pathname="/dashboard/live">
        <div className="flex items-center justify-center h-full">
          <div className="text-muted-foreground">Loading...</div>
        </div>
      </DashboardLayout>
    }>
      <LiveCallContent />
    </Suspense>
  );
}