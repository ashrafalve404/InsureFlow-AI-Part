"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { getDashboardStats, getCalls } from "@/lib/api";
import { formatRelativeTime, cn } from "@/lib/utils";
import { CallSession, DashboardStats as DashboardStatsType } from "@/lib/types";
import Link from "next/link";
import { 
  Phone, 
  AlertTriangle, 
  Shield, 
  TrendingUp,
  Users,
  ArrowRight,
  Play
} from "lucide-react";

export default function DashboardPage() {
  const pathname = "/dashboard";
  const [stats, setStats] = useState<DashboardStatsType | null>(null);
  const [sessions, setSessions] = useState<CallSession[]>([]);
  const [loading, setLoading] = useState(true);

  const statsConfig = stats ? [
  {
    name: "Active Calls",
    value: stats.active_calls,
    icon: Phone,
    color: "text-primary",
    bg: "bg-primary/10",
  },
  {
    name: "Sessions Today",
    value: stats.total_sessions_today,
    icon: TrendingUp,
    color: "text-emerald-600",
    bg: "bg-emerald-600/10",
  },
  {
    name: "Objections Today",
    value: stats.objections_flagged_today,
    icon: AlertTriangle,
    color: "text-amber-600",
    bg: "bg-amber-600/10",
  },
  {
    name: "Compliance Alerts",
    value: stats.compliance_alerts_today,
    icon: Shield,
    color: "text-red-600",
    bg: "bg-red-600/10",
  },
] : [];

  useEffect(() => {
    async function fetchData() {
      try {
        const [statsData, callsData] = await Promise.all([
          getDashboardStats(),
          getCalls(0, 10),
        ]);
        setStats(statsData);
        setSessions(callsData.sessions);
      } catch (error) {
        console.error("Failed to fetch dashboard data:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, []);
  
  const activeSessions = sessions.filter(s => s.status === "active");
  
  return (
    <DashboardLayout pathname={pathname}>
      {/* Header */}
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4 mb-6 lg:mb-8">
        <div>
          <h1 className="text-xl sm:text-2xl font-semibold">Dashboard</h1>
          <p className="text-sm sm:text-base text-muted-foreground">Welcome back! Here's your activity overview.</p>
        </div>
        <Link 
          href="/dashboard/live"
          className={cn(
            "flex items-center justify-center gap-2 px-4 py-2 rounded-lg w-full sm:w-auto",
            "bg-primary text-primary-foreground font-medium",
            "hover:bg-primary/90 transition-colors"
          )}
        >
          <Play className="w-4 h-4" />
          <span className="text-sm">Start New Call</span>
        </Link>
      </div>

      {/* Stats Grid */}
      {loading ? (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4 mb-6 lg:mb-8">
          {[1,2,3,4].map(i => (
            <div key={i} className="p-4 lg:p-6 rounded-xl lg:rounded-2xl border border-border bg-card animate-pulse">
              <div className="h-4 bg-muted rounded w-1/2 mb-4"></div>
              <div className="h-8 bg-muted rounded w-1/3"></div>
            </div>
          ))}
        </div>
      ) : (
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-3 lg:gap-4 mb-6 lg:mb-8">
          {statsConfig?.map((stat) => (
          <div
            key={stat.name}
            className={cn(
              "p-4 lg:p-6 rounded-xl lg:rounded-2xl border border-border bg-card",
              "hover:shadow-lg transition-shadow"
            )}
          >
            <div className="flex items-center justify-between mb-3 lg:mb-4">
              <span className="text-xs lg:text-sm font-medium text-muted-foreground">
                {stat.name}
              </span>
              <div className={cn("w-8 h-8 lg:w-10 lg:h-10 rounded-lg flex items-center justify-center", stat.bg)}>
                <stat.icon className={cn("w-4 h-4", stat.color)} />
              </div>
            </div>
            <p className="text-2xl lg:text-3xl font-semibold">{stat.value}</p>
          </div>
        ))}
        </div>
      )}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4 lg:gap-6">
        {/* Active Calls */}
        <div className="rounded-xl lg:rounded-2xl border border-border bg-card p-4 lg:p-6">
          <div className="flex items-center justify-between mb-4 lg:mb-6">
            <h2 className="text-base lg:text-lg font-semibold">Active Calls</h2>
            <Link 
              href="/dashboard/calls"
              className="text-sm text-primary hover:text-primary/80 font-medium flex items-center gap-1"
            >
              <span className="hidden sm:inline">View all</span> <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          
          {activeSessions.length === 0 && !loading ? (
            <div className="py-8 lg:py-12 text-center">
              <Phone className="w-10 h-10 lg:w-12 lg:h-12 mx-auto text-muted-foreground/50 mb-3" />
              <p className="text-muted-foreground mb-2">No active calls</p>
              <Link 
                href="/dashboard/live"
                className="text-sm text-primary hover:text-primary/80 font-medium"
              >
                Start a new call
              </Link>
            </div>
          ) : (
            <div className="space-y-3 lg:space-y-4">
              {activeSessions.map((session) => (
                <Link
                  key={session.id}
                  href={`/dashboard/live?id=${session.id}`}
                  className={cn(
                    "flex items-center gap-3 lg:gap-4 p-3 lg:p-4 rounded-xl",
                    "bg-muted/50 hover:bg-muted transition-colors",
                    "border border-transparent hover:border-border"
                  )}
                >
                  <div className="w-8 lg:w-10 h-8 lg:h-10 rounded-full bg-primary/10 flex items-center justify-center shrink-0">
                    <Users className="w-4 h-4 text-primary" />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className="font-medium text-sm lg:text-base truncate">{session.customer_name}</p>
                    <p className="text-xs lg:text-sm text-muted-foreground truncate">
                      {session.customer_phone} - {session.agent_name}
                    </p>
                  </div>
                  <div className="text-right shrink-0">
                    <p className="text-xs text-emerald-600 font-medium">Active</p>
                    <p className="text-xs text-muted-foreground">
                      {formatRelativeTime(session.started_at)}
                    </p>
                  </div>
                </Link>
              ))}
            </div>
          )}
        </div>

        {/* Recent Sessions */}
        <div className="rounded-xl lg:rounded-2xl border border-border bg-card p-4 lg:p-6">
          <div className="flex items-center justify-between mb-4 lg:mb-6">
            <h2 className="text-base lg:text-lg font-semibold">Recent Sessions</h2>
            <Link 
              href="/dashboard/calls"
              className="text-sm text-primary hover:text-primary/80 font-medium flex items-center gap-1"
            >
              <span className="hidden sm:inline">View all</span> <ArrowRight className="w-4 h-4" />
            </Link>
          </div>
          
          <div className="space-y-3 lg:space-y-4">
            {sessions && sessions.length > 0 ? (
              <>
                {sessions.slice(0, 5).map((session) => (
              <Link
                key={session.id}
                href={`/dashboard/calls/${session.id}`}
                className={cn(
                  "flex items-center gap-3 lg:gap-4 p-3 lg:p-4 rounded-xl",
                  "hover:bg-muted transition-colors"
                )}
              >
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-sm lg:text-base truncate">{session.customer_name}</p>
                  <p className="text-xs lg:text-sm text-muted-foreground truncate">
                    {session.agent_name}
                  </p>
                </div>
                <div className="text-right shrink-0">
                  <span className={cn(
                    "inline-flex px-2 py-1 rounded-full text-xs font-medium",
                    session.status === "active" 
                      ? "bg-emerald-600/10 text-emerald-600"
                      : "bg-muted text-muted-foreground"
                  )}>
                    {session.status}
                  </span>
                  <p className="text-xs text-muted-foreground mt-1">
                    {formatRelativeTime(session.started_at)}
                  </p>
                </div>
              </Link>
              ))}
              </>
            ) : (
              <p className="text-muted-foreground text-sm">No recent sessions</p>
            )}
          </div>
        </div>
      </div>
    </DashboardLayout>
  );
}