"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { getCalls, deleteCall } from "@/lib/api";
import { formatRelativeTime, cn } from "@/lib/utils";
import { CallSession } from "@/lib/types";
import Link from "next/link";
import { Phone, Users, Clock, ArrowRight, Trash2 } from "lucide-react";
import { DeleteConfirmModal } from "@/components/modals/delete-confirm-modal";

export default function CallsPage() {
  const pathname = "/dashboard/calls";
  const [sessions, setSessions] = useState<CallSession[]>([]);
  const [loading, setLoading] = useState(true);
  
  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [sessionToDelete, setSessionToDelete] = useState<number | null>(null);
  const [isDeleting, setIsDeleting] = useState(false);

  useEffect(() => {
    async function fetchCalls() {
      try {
        const data = await getCalls(0, 50);
        setSessions(data.sessions);
      } catch (error) {
        console.error("Failed to fetch calls:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchCalls();
  }, []);

  const handleDeleteSession = async () => {
    if (!sessionToDelete) return;

    setIsDeleting(true);
    try {
      await deleteCall(sessionToDelete);
      setSessions((prev) => prev.filter((s) => s.id !== sessionToDelete));
      setIsModalOpen(false);
    } catch (error) {
      console.error("Failed to delete session:", error);
      alert("Failed to delete session.");
    } finally {
      setIsDeleting(false);
      setSessionToDelete(null);
    }
  };

  const openDeleteModal = (id: number) => {
    setSessionToDelete(id);
    setIsModalOpen(true);
  };
  
  return (
    <DashboardLayout pathname={pathname}>
      <div className="p-8">
        <div className="flex items-center justify-between mb-8">
          <div>
            <h1 className="text-2xl font-semibold">Call Sessions</h1>
            <p className="text-muted-foreground">View all call history and details</p>
          </div>
        </div>

        {/* Sessions List */}
        <div className="rounded-2xl border border-border bg-card overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full">
              <thead>
                <tr className="border-b border-border bg-muted/50">
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Session</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Customer</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Agent</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Status</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Started</th>
                  <th className="text-left px-6 py-4 text-sm font-medium text-muted-foreground">Actions</th>
                </tr>
              </thead>
              <tbody>
                {loading ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-muted-foreground">
                      Loading...
                    </td>
                  </tr>
                ) : sessions.length === 0 ? (
                  <tr>
                    <td colSpan={6} className="px-6 py-8 text-center text-muted-foreground">
                      No calls found. Start a new call from the Live page.
                    </td>
                  </tr>
                ) : (
                  <>
                    {sessions.map((session) => (
                      <tr key={session.id} className="border-b border-border hover:bg-muted/30">
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-3">
                            <div className="w-10 h-10 rounded-full bg-primary/10 flex items-center justify-center">
                              <Phone className="w-5 h-5 text-primary" />
                            </div>
                            <div>
                              <p className="font-medium">#{session.id}</p>
                              <p className="text-xs text-muted-foreground">
                                {session.call_sid || "No SID"}
                              </p>
                            </div>
                          </div>
                        </td>
                        <td className="px-6 py-4">
                          <p className="font-medium">{session.customer_name}</p>
                          <p className="text-sm text-muted-foreground">{session.customer_phone}</p>
                        </td>
                        <td className="px-6 py-4">
                          <p className="font-medium">{session.agent_name}</p>
                        </td>
                        <td className="px-6 py-4">
                          <span className={cn(
                            "inline-flex items-center gap-1.5 px-2 py-1 rounded-full text-xs font-medium",
                            session.status === "active" 
                              ? "bg-red-500/10 text-red-500 border border-red-500/20"
                              : "bg-muted text-muted-foreground"
                          )}>
                            {session.status === "active" && <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />}
                            {session.status === "active" ? "Live" : session.status}
                          </span>
                        </td>
                        <td className="px-6 py-4">
                          <p className="text-sm text-muted-foreground">
                            {formatRelativeTime(session.started_at)}
                          </p>
                        </td>
                        <td className="px-6 py-4">
                          <div className="flex items-center gap-4">
                            <Link 
                              href={`/dashboard/live?id=${session.id}`}
                              className="inline-flex items-center gap-1 text-sm text-primary hover:text-primary/80 font-medium"
                            >
                              View <ArrowRight className="w-4 h-4" />
                            </Link>
                            <button
                              onClick={() => openDeleteModal(session.id)}
                              className="p-1.5 text-muted-foreground hover:text-red-500 hover:bg-red-500/10 rounded-lg transition-colors"
                              title="Delete Session"
                            >
                              <Trash2 className="w-4 h-4" />
                            </button>
                          </div>
                        </td>
                      </tr>
                    ))}
                  </>
                )}
              </tbody>
            </table>
          </div>
        </div>
      </div>

      <DeleteConfirmModal 
        isOpen={isModalOpen}
        onClose={() => setIsModalOpen(false)}
        onConfirm={handleDeleteSession}
        loading={isDeleting}
      />
    </DashboardLayout>
  );
}