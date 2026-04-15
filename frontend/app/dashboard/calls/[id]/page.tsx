"use client";

import { use } from "react";
import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { getCall, getTranscripts, getSuggestions, lookupContactByPhone } from "@/lib/api";
import { formatRelativeTime, formatTime, cn, generateInitials } from "@/lib/utils";
import { CallSession, TranscriptChunk, AISuggestion, CRMContact, PostCallSummary } from "@/lib/types";
import Link from "next/link";
import { 
  Phone, 
  User, 
  AlertTriangle, 
  Shield,
  Clock,
  Tag,
  Building,
  ArrowLeft,
  MessageSquare
} from "lucide-react";

export default function CallDetailPage({ params }: { params: Promise<{ id: string }> }) {
  const resolvedParams = use(params);
  const sessionId = parseInt(resolvedParams.id);
  const pathname = "/dashboard/calls";
  
  const [session, setSession] = useState<CallSession | null>(null);
  const [transcripts, setTranscripts] = useState<TranscriptChunk[]>([]);
  const [suggestions, setSuggestions] = useState<AISuggestion[]>([]);
  const [crmContact, setCrmContact] = useState<CRMContact | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    async function fetchData() {
      try {
        const [sessionData, transcriptData, suggestionData] = await Promise.all([
          getCall(sessionId),
          getTranscripts(sessionId),
          getSuggestions(sessionId),
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
      } catch (err) {
        setError("Failed to load session data");
        console.error(err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [sessionId]);

  if (loading) {
    return (
      <DashboardLayout pathname={pathname}>
        <div className="flex items-center justify-center py-12">
          <div className="text-muted-foreground">Loading...</div>
        </div>
      </DashboardLayout>
    );
  }

  if (error || !session) {
    return (
      <DashboardLayout pathname={pathname}>
        <div className="text-center py-12">
          <Phone className="w-12 h-12 mx-auto text-muted-foreground/50 mb-4" />
          <h1 className="text-xl font-semibold mb-2">Session not found</h1>
          <p className="text-muted-foreground mb-4">The session you're looking for doesn't exist.</p>
          <Link href="/dashboard/calls" className="text-primary hover:underline">
            Back to calls
          </Link>
        </div>
      </DashboardLayout>
    );
  }

  return (
    <DashboardLayout pathname={pathname}>
      <div className="space-y-4 lg:space-y-6">
        {/* Header */}
        <div className="flex items-center gap-4">
          <Link 
            href="/dashboard/calls"
            className="p-2 rounded-lg hover:bg-muted"
          >
            <ArrowLeft className="w-5 h-5" />
          </Link>
          <div>
            <h1 className="text-xl lg:text-2xl font-semibold">Session #{session.id}</h1>
            <p className="text-sm lg:text-base text-muted-foreground">
              {session.customer_name} - {session.customer_phone}
            </p>
          </div>
          <span className={cn(
            "ml-auto inline-flex px-3 py-1 rounded-full text-sm font-medium",
            session.status === "active" 
              ? "bg-emerald-600/10 text-emerald-600"
              : "bg-muted text-muted-foreground"
          )}>
            {session.status}
          </span>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
          {/* Session Details */}
          <div className="rounded-xl lg:rounded-2xl border border-border bg-card p-4 lg:p-6">
            <h2 className="text-base lg:text-lg font-semibold mb-4">Session Details</h2>
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">Customer</span>
                <span className="font-medium">{session.customer_name}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">Phone</span>
                <span className="font-medium">{session.customer_phone}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">Agent</span>
                <span className="font-medium">{session.agent_name}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-muted-foreground">Started</span>
                <span className="font-medium">{formatRelativeTime(session.started_at)}</span>
              </div>
              {session.call_sid && (
                <div className="flex items-center justify-between py-2">
                  <span className="text-muted-foreground">Call SID</span>
                  <span className="text-sm font-mono">{session.call_sid}</span>
                </div>
              )}
            </div>
          </div>

          {/* CRM Context */}
          <div className="rounded-xl lg:rounded-2xl border border-border bg-card p-4 lg:p-6">
            <h2 className="text-base lg:text-lg font-semibold mb-4">CRM Context</h2>
            {crmContact ? (
              <div className="space-y-3">
                <div className="flex items-center gap-3">
                  <div className="w-12 h-12 rounded-full bg-primary/10 flex items-center justify-center text-lg font-semibold text-primary">
                    {generateInitials(crmContact.full_name || "")}
                  </div>
                  <div>
                    <p className="font-semibold">{crmContact.full_name}</p>
                    <p className="text-sm text-muted-foreground">{crmContact.email}</p>
                  </div>
                </div>
                <div className="flex items-center gap-2">
                  <Building className="w-4 h-4 text-muted-foreground" />
                  <span className="text-sm">{crmContact.pipeline_stage}</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {crmContact.tags.map((tag) => (
                    <span key={tag} className="px-2 py-1 rounded-full text-xs bg-muted">
                      <Tag className="w-3 h-3 inline mr-1" />
                      {tag}
                    </span>
                  ))}
                </div>
                {crmContact.notes_summary && (
                  <div className="p-3 rounded-xl bg-muted/50">
                    <p className="text-xs font-medium mb-1">Notes</p>
                    <p className="text-sm">{crmContact.notes_summary}</p>
                  </div>
                )}
              </div>
            ) : (
              <p className="text-muted-foreground">No CRM data</p>
            )}
          </div>
        </div>

        {/* Transcripts */}
        <div className="rounded-xl lg:rounded-2xl border border-border bg-card p-4 lg:p-6">
          <h2 className="text-base lg:text-lg font-semibold mb-4">Transcripts</h2>
          {transcripts.length > 0 ? (
            <div className="space-y-3 max-h-96 overflow-y-auto">
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
                    "max-w-[80%] px-4 py-3 rounded-2xl text-sm",
                    chunk.speaker === "agent"
                      ? "bg-primary text-primary-foreground rounded-br-md"
                      : "bg-muted rounded-bl-md"
                  )}>
                    {chunk.text}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No transcripts available</p>
          )}
        </div>

        {/* Suggestions */}
        <div className="rounded-xl lg:rounded-2xl border border-border bg-card p-4 lg:p-6">
          <h2 className="text-base lg:text-lg font-semibold mb-4">AI Suggestions</h2>
          {suggestions.length > 0 ? (
            <div className="space-y-3">
              {suggestions.map((suggestion, i) => (
                <div key={i} className="p-4 rounded-xl bg-muted/30">
                  <div className="flex items-center gap-2 mb-2">
                    <MessageSquare className="w-4 h-4 text-primary" />
                    <span className="text-xs text-muted-foreground">
                      {formatTime(suggestion.created_at)}
                    </span>
                  </div>
                  <p className="text-sm mb-2">{suggestion.suggested_response}</p>
                  <div className="flex items-center gap-2 flex-wrap">
                    <span className="text-xs px-2 py-1 rounded-full bg-muted capitalize">
                      {suggestion.call_stage}
                    </span>
                    {suggestion.objection_label !== "none" && (
                      <span className="text-xs px-2 py-1 rounded-full bg-amber-600/10 text-amber-600">
                        <AlertTriangle className="w-3 h-3 inline mr-1" />
                        {suggestion.objection_label}
                      </span>
                    )}
                    {suggestion.compliance_warning && (
                      <span className="text-xs px-2 py-1 rounded-full bg-red-600/10 text-red-600">
                        <Shield className="w-3 h-3 inline mr-1" />
                        Compliance
                      </span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          ) : (
            <p className="text-muted-foreground">No suggestions available</p>
          )}
        </div>
      </div>
    </DashboardLayout>
  );
}