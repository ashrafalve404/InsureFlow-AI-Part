"use client";

import { useEffect, useState, use } from "react";
import { Suspense } from "react";
import { useSearchParams } from "next/navigation";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { getCall, getTranscripts, getSuggestions, lookupContactByPhone, startCall } from "@/lib/api";
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
  
  const [sessionId, setSessionId] = useState<number | null>(initialSessionId);
  const [session, setSession] = useState<CallSession | null>(null);
  const [transcripts, setTranscripts] = useState<TranscriptChunk[]>([]);
  const [suggestions, setSuggestions] = useState<AISuggestion[]>([]);
  const [crmContact, setCrmContact] = useState<CRMContact | null>(null);
  const [loading, setLoading] = useState(!!initialSessionId);
  const [manualInput, setManualInput] = useState("");
  const [activePanel, setActivePanel] = useState<"transcript" | "ai" | "crm">("transcript");

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
        setTranscripts(transcriptData);
        setSuggestions(suggestionData);
        
        if (sessionData.customer_phone) {
          try {
            const crm = await lookupContactByPhone(sessionData.customer_phone);
            if (crm.contact_found) {
              setCrmContact(crm);
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
  }, [sessionId]);

  const latestSuggestion = suggestions && suggestions.length > 0 ? suggestions[suggestions.length - 1] : null;
  const callStage = latestSuggestion?.call_stage || "unknown";

  const handleManualSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!manualInput.trim()) return;
    console.log("Manual input:", manualInput);
    setManualInput("");
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
                  <span className={session.status === "active" ? "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-emerald-600/10 text-emerald-600" : "inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-muted"}>
                    {session.status === "active" && <span className="w-1.5 h-1.5 rounded-full bg-emerald-600 animate-pulse" />}
                    {session.status === "active" ? "Live" : session.status}
                  </span>
                  <span className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-muted">
                    <Clock className="w-3 h-3" />
                    {callStage}
                  </span>
                </div>
              </>
            ) : (
              <div className="text-muted-foreground">No session selected</div>
            )}
          </div>

          {/* Transcript Stream */}
          <div className="flex-1 overflow-y-auto p-3 lg:p-4 space-y-3 lg:space-y-4">
            {loading ? (
              <div className="text-center py-8 text-muted-foreground">Loading...</div>
            ) : !transcripts || transcripts.length === 0 ? (
              <div className="text-center py-8 text-muted-foreground">No transcripts yet. Start a call to see live transcripts.</div>
            ) : (
              <>
                {transcripts.map((chunk) => (
              <div
                key={chunk.id}
                className={cn(
                  "flex flex-col",
                  chunk.speaker === "agent" ? "items-end" : "items-start"
                )}
              >
                <div className="flex items-center gap-2 mb-1">
                  <span className={cn(
                    "text-xs font-medium",
                    chunk.speaker === "agent" ? "text-primary" : "text-muted-foreground"
                  )}>
                    {chunk.speaker === "agent" ? "You" : chunk.speaker}
                  </span>
                  <span className="text-xs text-muted-foreground">
                    {formatTime(chunk.timestamp)}
                  </span>
                </div>
                <div className={cn(
                  "max-w-[85%] px-3 lg:px-4 py-2 lg:py-3 rounded-xl lg:rounded-2xl text-sm",
                  chunk.speaker === "agent"
                    ? "bg-primary text-primary-foreground rounded-br-md"
                    : "bg-muted rounded-bl-md"
                )}>
                  {chunk.text}
                </div>
              </div>
              ))}
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
                placeholder="Type a message to test..."
                className="flex-1 px-3 lg:px-4 py-2 rounded-xl border border-border bg-background text-sm"
              />
              <button 
                type="submit"
                className="px-3 lg:px-4 py-2 rounded-xl bg-primary text-primary-foreground"
              >
                <Send className="w-4 h-4" />
              </button>
            </div>
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
              <MessageSquare className="w-4 h-4" />
              AI Suggestion
            </h3>
          </div>

          <div className="flex-1 overflow-y-auto p-3 lg:p-4">
            {latestSuggestion ? (
              <div className="space-y-3 lg:space-y-4">
                {/* Current Suggestion */}
                <div className="p-3 lg:p-4 rounded-xl lg:rounded-2xl bg-gradient-to-br from-primary/10 to-primary/5 border border-primary/20">
                  <div className="flex items-center gap-2 mb-2">
                    <span className="text-xs font-medium text-primary">Suggested Response</span>
                    <span className="text-xs text-muted-foreground">
                      {formatTime(latestSuggestion.created_at)}
                    </span>
                  </div>
                  <p className="text-base lg:text-lg font-medium">{latestSuggestion.suggested_response}</p>
                </div>

                {/* Call Stage */}
                <div className="flex items-center gap-2 p-2 lg:p-3 rounded-xl bg-muted/50">
                  <Clock className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">Current stage:</span>
                  <span className="text-sm font-medium capitalize">{callStage}</span>
                </div>

                {/* Objection */}
                {latestSuggestion.objection_label !== "none" && (
                  <div className="flex items-center gap-2 p-2 lg:p-3 rounded-xl bg-amber-600/10">
                    <AlertTriangle className="w-4 h-4 text-amber-600" />
                    <span className="text-sm font-medium text-amber-600">
                      Objection: {latestSuggestion.objection_label}
                    </span>
                  </div>
                )}

                {/* Compliance */}
                {latestSuggestion.compliance_warning && (
                  <div className="flex items-center gap-2 p-2 lg:p-3 rounded-xl bg-red-600/10">
                    <Shield className="w-4 h-4 text-red-600" />
                    <span className="text-sm font-medium text-red-600">
                      {latestSuggestion.compliance_warning}
                    </span>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-8 lg:py-12 text-center">
                <MessageSquare className="w-10 lg:w-12 h-10 lg:h-12 mx-auto text-muted-foreground/50 mb-3" />
                <p className="text-muted-foreground">Waiting for transcript...</p>
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
              <User className="w-4 h-4" />
              CRM Context
            </h3>
            
            {crmContact ? (
              <div className="space-y-2 lg:space-y-3">
                <div className="flex items-center gap-2 lg:gap-3">
                  <div className="w-10 lg:w-12 h-10 lg:h-12 rounded-full bg-primary/10 flex items-center justify-center text-sm lg:text-lg font-semibold text-primary shrink-0">
                    {generateInitials(crmContact.full_name || "")}
                  </div>
                  <div className="min-w-0">
                    <p className="font-medium text-sm lg:text-base truncate">{crmContact.full_name}</p>
                    <p className="text-xs lg:text-sm text-muted-foreground truncate">{crmContact.email}</p>
                  </div>
                </div>

                {/* Tags */}
                <div className="flex flex-wrap gap-1">
                  {crmContact.tags.map((tag) => (
                    <span 
                      key={tag}
                      className="inline-flex items-center gap-1 px-2 py-1 rounded-full text-xs font-medium bg-muted"
                    >
                      <Tag className="w-3 h-3" />
                      {tag}
                    </span>
                  ))}
                </div>

                {/* Pipeline Stage */}
                <div className="flex items-center gap-2 p-2 lg:p-3 rounded-xl bg-muted/50">
                  <Building className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">{crmContact.pipeline_stage}</span>
                </div>

                {/* Notes */}
                {crmContact.notes_summary && (
                  <div className="p-2 lg:p-3 rounded-xl bg-muted/50">
                    <p className="text-xs font-medium mb-1">Notes</p>
                    <p className="text-sm text-muted-foreground">{crmContact.notes_summary}</p>
                  </div>
                )}
              </div>
            ) : (
              <div className="py-6 lg:py-8 text-center">
                <User className="w-8 lg:w-10 h-8 lg:h-10 mx-auto text-muted-foreground/50 mb-2" />
                <p className="text-sm text-muted-foreground">No CRM data</p>
              </div>
            )}
          </div>

          {/* Recent Suggestions History */}
          <div className="flex-1 overflow-y-auto p-3 lg:p-4">
            <h3 className="font-semibold text-sm mb-2 lg:mb-3">Previous Suggestions</h3>
            <div className="space-y-2">
              {suggestions && suggestions.length > 1 ? (
                <>
                  {suggestions.slice(0, -1).map((suggestion, i) => (
                <div 
                  key={i}
                  className="p-2 lg:p-3 rounded-xl bg-muted/30 hover:bg-muted/50 cursor-pointer transition-colors"
                >
                  <p className="text-sm line-clamp-2">{suggestion.suggested_response}</p>
                  <div className="flex items-center gap-2 mt-1 lg:mt-2">
                    <span className="text-xs text-muted-foreground capitalize">{suggestion.call_stage}</span>
                    {suggestion.objection_label !== "none" && (
                      <span className="text-xs text-amber-600">{suggestion.objection_label}</span>
                    )}
                  </div>
                </div>
              ))}
                </>
              ) : (
                <p className="text-sm text-muted-foreground">No previous suggestions</p>
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