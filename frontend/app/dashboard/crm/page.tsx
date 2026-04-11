"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { cn } from "@/lib/utils";
import { Search, User, Mail, Phone, Tag, CheckCircle, XCircle, Loader2 } from "lucide-react";

interface CRMStatus {
  enabled: boolean;
  provider: string;
  configured: boolean;
  token_present: boolean;
}

interface Contact {
  contact_found: boolean;
  contact_id?: string;
  full_name?: string;
  first_name?: string;
  last_name?: string;
  phone?: string;
  email?: string;
  tags?: string[];
  notes_summary?: string;
  custom_fields?: Record<string, string>;
  pipeline_stage?: string;
  source?: string;
}

export default function CRMPage() {
  const pathname = "/dashboard/crm";
  const [status, setStatus] = useState<CRMStatus | null>(null);
  const [searchType, setSearchType] = useState<"phone" | "email">("phone");
  const [query, setQuery] = useState("");
  const [contact, setContact] = useState<Contact | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState("");

  const fetchStatus = async () => {
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1/crm/status`);
      const data = await res.json();
      setStatus(data);
    } catch (err) {
      console.error("Failed to fetch CRM status:", err);
    }
  };

  const handleSearch = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!query.trim()) return;
    
    setLoading(true);
    setError("");
    setContact(null);
    
    try {
      const endpoint = searchType === "phone" 
        ? `/api/v1/crm/contact/by-phone?phone=${encodeURIComponent(query)}`
        : `/api/v1/crm/contact/by-email?email=${encodeURIComponent(query)}`;
      
      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}${endpoint}`);
      const data = await res.json();
      
      if (res.ok) {
        setContact(data);
      } else {
        setError(data.detail || "Search failed");
      }
    } catch (err) {
      setError("Failed to search contact");
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <DashboardLayout pathname={pathname}>
      <div className="max-w-2xl mx-auto">
        <div className="mb-6 lg:mb-8">
          <h1 className="text-xl lg:text-2xl font-semibold mb-2">CRM Integration</h1>
          <p className="text-sm lg:text-base text-muted-foreground">
            Look up contacts from {status?.provider || "your CRM"}
          </p>
        </div>

        <div className="rounded-xl lg:rounded-2xl border border-border bg-card p-4 lg:p-6 mb-4 lg:mb-6">
          <h2 className="text-base lg:text-lg font-semibold mb-4">Connection Status</h2>
          
          {status ? (
            <div className="space-y-3">
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-sm lg:text-base text-muted-foreground">Provider</span>
                <span className="text-sm lg:text-base font-medium">{status.provider}</span>
              </div>
              <div className="flex items-center justify-between py-2 border-b border-border">
                <span className="text-sm lg:text-base text-muted-foreground">Status</span>
                <div className="flex items-center gap-2">
                  {status.configured ? (
                    <CheckCircle className="w-4 h-4 text-emerald-600" />
                  ) : (
                    <XCircle className="w-4 h-4 text-red-600" />
                  )}
                  <span className={cn("text-sm lg:text-base", status.configured ? "text-emerald-600" : "text-red-600")}>
                    {status.configured ? "Connected" : "Not Configured"}
                  </span>
                </div>
              </div>
              <div className="flex items-center justify-between py-2">
                <span className="text-sm lg:text-base text-muted-foreground">Token</span>
                <span className={cn("text-sm lg:text-base", status.token_present ? "text-emerald-600" : "text-red-600")}>
                  {status.token_present ? "Present" : "Missing"}
                </span>
              </div>
            </div>
          ) : (
            <p className="text-sm lg:text-base text-muted-foreground">Loading...</p>
          )}
        </div>

        <div className="rounded-xl lg:rounded-2xl border border-border bg-card p-4 lg:p-6 mb-4 lg:mb-6">
          <h2 className="text-base lg:text-lg font-semibold mb-4">Search Contact</h2>
          
          <form onSubmit={handleSearch} className="space-y-4">
            <div className="flex gap-2">
              <button
                type="button"
                onClick={() => setSearchType("phone")}
                className={cn(
                  "flex-1 py-2 rounded-lg text-sm font-medium",
                  searchType === "phone"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                )}
              >
                By Phone
              </button>
              <button
                type="button"
                onClick={() => setSearchType("email")}
                className={cn(
                  "flex-1 py-2 rounded-lg text-sm font-medium",
                  searchType === "email"
                    ? "bg-primary text-primary-foreground"
                    : "bg-muted text-muted-foreground"
                )}
              >
                By Email
              </button>
            </div>
            
            <div className="flex gap-2">
              <input
                type={searchType === "phone" ? "tel" : "email"}
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder={searchType === "phone" ? "+1234567890" : "email@example.com"}
                className="flex-1 px-3 lg:px-4 py-2 rounded-xl border border-border bg-background text-sm"
              />
              <button
                type="submit"
                disabled={loading || !status?.configured}
                className={cn(
                  "px-4 py-2 rounded-xl bg-primary text-primary-foreground",
                  "hover:bg-primary/90 transition-colors",
                  "disabled:opacity-50 disabled:cursor-not-allowed"
                )}
              >
                {loading ? <Loader2 className="w-4 h-4 animate-spin" /> : <Search className="w-4 h-4" />}
              </button>
            </div>
          </form>
          
          {error && (
            <p className="text-red-500 text-sm mt-3">{error}</p>
          )}
        </div>

        {contact && (
          <div className="rounded-xl lg:rounded-2xl border border-border bg-card p-4 lg:p-6">
            <h2 className="text-base lg:text-lg font-semibold mb-4">Contact Details</h2>
            
            {!contact.contact_found ? (
              <p className="text-muted-foreground">No contact found</p>
            ) : (
              <div className="space-y-3">
                <div className="flex items-center gap-3 pb-3 border-b border-border">
                  <div className="w-10 lg:w-12 h-10 lg:h-12 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <User className="w-5 lg:w-6 h-5 lg:h-6 text-primary" />
                  </div>
                  <div>
                    <p className="font-semibold text-base lg:text-lg">{contact.full_name}</p>
                    <p className="text-sm text-muted-foreground">{contact.pipeline_stage}</p>
                  </div>
                </div>
                
                {contact.phone && (
                  <div className="flex items-center gap-3 py-2">
                    <Phone className="w-4 h-4 text-muted-foreground shrink-0" />
                    <span className="text-sm lg:text-base">{contact.phone}</span>
                  </div>
                )}
                
                {contact.email && (
                  <div className="flex items-center gap-3 py-2">
                    <Mail className="w-4 h-4 text-muted-foreground shrink-0" />
                    <span className="text-sm lg:text-base">{contact.email}</span>
                  </div>
                )}
                
                {contact.tags && contact.tags.length > 0 && (
                  <div className="flex items-start gap-3 py-2">
                    <Tag className="w-4 h-4 text-muted-foreground mt-0.5 shrink-0" />
                    <div className="flex flex-wrap gap-2">
                      {contact.tags.map((tag) => (
                        <span key={tag} className="px-2 py-1 rounded-full text-xs lg:text-sm bg-muted">
                          {tag}
                        </span>
                      ))}
                    </div>
                  </div>
                )}
                
                {contact.notes_summary && (
                  <div className="pt-3 border-t border-border">
                    <p className="text-sm text-muted-foreground mb-1">Notes</p>
                    <p className="text-sm lg:text-base">{contact.notes_summary}</p>
                  </div>
                )}
              </div>
            )}
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}