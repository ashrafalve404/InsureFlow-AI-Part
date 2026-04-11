"use client";

import { useState, useEffect } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { cn } from "@/lib/utils";
import { FileText, RefreshCw, CheckCircle, XCircle, Loader2 } from "lucide-react";

interface RAGStatus {
  enabled: boolean;
  vector_store_exists: boolean;
  indexed_file_count: number;
  total_chunks: number;
}

export default function KnowledgePage() {
  const pathname = "/dashboard/knowledge";
  const [status, setStatus] = useState<RAGStatus | null>(null);
  const [loading, setLoading] = useState(false);
  const [ingesting, setIngesting] = useState(false);

  const fetchStatus = async () => {
    setLoading(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1/rag/status`);
      const data = await res.json();
      setStatus(data);
    } catch (error) {
      console.error("Failed to fetch RAG status:", error);
    } finally {
      setLoading(false);
    }
  };

  const triggerIngest = async () => {
    setIngesting(true);
    try {
      const res = await fetch(`${process.env.NEXT_PUBLIC_BACKEND_URL}/api/v1/rag/ingest`, {
        method: "POST",
      });
      if (res.ok) {
        await fetchStatus();
      }
    } catch (error) {
      console.error("Ingest failed:", error);
    } finally {
      setIngesting(false);
    }
  };

  useEffect(() => {
    fetchStatus();
  }, []);

  return (
    <DashboardLayout pathname={pathname}>
      <div className="max-w-2xl mx-auto">
        <div className="flex items-center justify-between mb-6 lg:mb-8">
          <div>
            <h1 className="text-xl lg:text-2xl font-semibold mb-2">Knowledge Base</h1>
            <p className="text-sm lg:text-base text-muted-foreground">
              Manage your RAG document index
            </p>
          </div>
        </div>

        <div className="rounded-xl lg:rounded-2xl border border-border bg-card p-4 lg:p-6 mb-4 lg:mb-6">
          <h2 className="text-base lg:text-lg font-semibold mb-4">Index Status</h2>
          
          {loading ? (
            <div className="flex items-center gap-2 text-muted-foreground">
              <Loader2 className="w-4 lg:w-5 h-4 lg:h-5 animate-spin" />
              <span className="text-sm">Loading...</span>
            </div>
          ) : status ? (
            <div className="space-y-3 lg:space-y-4">
              <div className="flex items-center justify-between py-2 lg:py-3 border-b border-border">
                <span className="text-sm lg:text-base text-muted-foreground">Status</span>
                <div className="flex items-center gap-2">
                  {status.enabled ? (
                    <CheckCircle className="w-4 lg:w-5 h-4 lg:h-5 text-emerald-600" />
                  ) : (
                    <XCircle className="w-4 lg:w-5 h-4 lg:h-5 text-red-600" />
                  )}
                  <span className={cn("text-sm lg:text-base", status.enabled ? "text-emerald-600" : "text-red-600")}>
                    {status.enabled ? "Enabled" : "Disabled"}
                  </span>
                </div>
              </div>
              
              <div className="flex items-center justify-between py-2 lg:py-3 border-b border-border">
                <span className="text-sm lg:text-base text-muted-foreground">Vector Store</span>
                <span className="text-sm lg:text-base">
                  {status.vector_store_exists ? (
                    <span className="text-emerald-600">Ready</span>
                  ) : (
                    <span className="text-amber-600">Not Created</span>
                  )}
                </span>
              </div>
              
              <div className="flex items-center justify-between py-2 lg:py-3 border-b border-border">
                <span className="text-sm lg:text-base text-muted-foreground">Indexed Files</span>
                <span className="text-sm lg:text-base font-medium">{status.indexed_file_count}</span>
              </div>
              
              <div className="flex items-center justify-between py-2 lg:py-3">
                <span className="text-sm lg:text-base text-muted-foreground">Total Chunks</span>
                <span className="text-sm lg:text-base font-medium">{status.total_chunks}</span>
              </div>
            </div>
          ) : (
            <p className="text-sm lg:text-base text-muted-foreground">Unable to load status</p>
          )}
        </div>

        <div className="rounded-xl lg:rounded-2xl border border-border bg-card p-4 lg:p-6">
          <h2 className="text-base lg:text-lg font-semibold mb-4">Actions</h2>
          
          <button
            onClick={triggerIngest}
            disabled={ingesting}
            className={cn(
              "flex items-center gap-2 px-4 py-2 rounded-xl w-full sm:w-auto justify-center",
              "bg-primary text-primary-foreground font-medium",
              "hover:bg-primary/90 transition-colors",
              "disabled:opacity-50 disabled:cursor-not-allowed"
            )}
          >
            {ingesting ? (
              <Loader2 className="w-4 h-4 animate-spin" />
            ) : (
              <RefreshCw className="w-4 h-4" />
            )}
            {ingesting ? "Ingesting..." : "Re-ingest Documents"}
          </button>
          
          <p className="text-xs lg:text-sm text-muted-foreground mt-3">
            Place DOCX files in the knowledge/raw/ folder before running
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}