"use client";

import { useState } from "react";
import Link from "next/link";
import { useTheme } from "@/lib/hooks/use-theme";
import { 
  LayoutDashboard, 
  Phone, 
  Users, 
  BookOpen, 
  AlertTriangle, 
  Settings,
  Play,
  Activity,
  Headphones,
  Moon,
  Sun,
  Menu,
  X
} from "lucide-react";
import { cn } from "@/lib/utils";

const navigation = [
  { name: "Dashboard", href: "/dashboard", icon: LayoutDashboard },
  { name: "Live Assistant", href: "/dashboard/live", icon: Phone },
  { name: "Call Sessions", href: "/dashboard/calls", icon: Activity },
  { name: "CRM Context", href: "/dashboard/crm", icon: Users },
  { name: "Knowledge Base", href: "/dashboard/knowledge", icon: BookOpen },
  { name: "Alerts", href: "/dashboard/alerts", icon: AlertTriangle },
  { name: "Settings", href: "/dashboard/settings", icon: Settings },
];

const secondaryNav = [
  { name: "Demo Mode", href: "/dashboard/demo", icon: Play },
];

export function DashboardLayout({ children, pathname }: { children: React.ReactNode; pathname?: string }) {
  const { theme, toggleTheme } = useTheme();
  const [sidebarOpen, setSidebarOpen] = useState(false);

  return (
    <div className="flex min-h-screen bg-background">
      {/* Mobile overlay */}
      {sidebarOpen && (
        <div 
          className="fixed inset-0 z-40 bg-black/50 lg:hidden"
          onClick={() => setSidebarOpen(false)}
        />
      )}

      {/* Sidebar */}
      <aside className={cn(
        "fixed lg:static inset-y-0 left-0 z-50 w-64 border-r border-border bg-card flex flex-col",
        "transform transition-transform duration-200 ease-in-out",
        "lg:translate-x-0",
        sidebarOpen ? "translate-x-0" : "-translate-x-full"
      )}>
        {/* Logo */}
        <div className="h-16 flex items-center justify-between gap-3 px-4 lg:px-6 border-b border-border">
          <div className="flex items-center gap-3">
            {/* Mobile close button */}
            <button 
              className="lg:hidden p-1 -ml-1"
              onClick={() => setSidebarOpen(false)}
            >
              <X className="w-5 h-5" />
            </button>
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center shrink-0">
              <Headphones className="w-5 h-5 text-primary-foreground" />
            </div>
            <div className="hidden sm:block">
              <h1 className="font-semibold text-lg">InsureFlow</h1>
              <p className="text-xs text-muted-foreground">AI Assistant</p>
            </div>
          </div>
          <button
            onClick={toggleTheme}
            className="w-8 h-8 rounded-lg flex items-center justify-center text-muted-foreground hover:bg-muted hover:text-foreground transition-colors"
            aria-label="Toggle theme"
          >
            {theme === "light" ? <Moon className="w-5 h-5" /> : <Sun className="w-5 h-5" />}
          </button>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-4 space-y-1 overflow-y-auto">
          {navigation.map((item) => {
            const isActive = pathname === item.href;
            return (
              <Link
                key={item.name}
                href={item.href}
                onClick={() => setSidebarOpen(false)}
                className={cn(
                  "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                  isActive
                    ? "bg-primary/10 text-primary"
                    : "text-muted-foreground hover:bg-muted hover:text-foreground"
                )}
              >
                <item.icon className="w-5 h-5 shrink-0" />
                <span className="truncate">{item.name}</span>
              </Link>
            );
          })}
          
          <div className="pt-4 mt-4 border-t border-border">
            <p className="px-3 pb-2 text-xs font-medium text-muted-foreground uppercase">
              Testing
            </p>
            {secondaryNav.map((item) => {
              const isActive = pathname === item.href;
              return (
                <Link
                  key={item.name}
                  href={item.href}
                  onClick={() => setSidebarOpen(false)}
                  className={cn(
                    "flex items-center gap-3 px-3 py-2 rounded-lg text-sm font-medium transition-colors",
                    isActive
                      ? "bg-primary/10 text-primary"
                      : "text-muted-foreground hover:bg-muted hover:text-foreground"
                  )}
                >
                  <item.icon className="w-5 h-5 shrink-0" />
                  <span className="truncate">{item.name}</span>
                </Link>
              );
            })}
          </div>
        </nav>

        {/* Footer */}
        <div className="p-4 border-t border-border">
          <div className="flex items-center gap-3 px-3 py-2">
            <div className="w-8 h-8 rounded-full bg-muted flex items-center justify-center text-sm font-medium shrink-0">
              SA
            </div>
            <div className="flex-1 min-w-0">
              <p className="text-sm font-medium truncate">Sarah Agent</p>
              <p className="text-xs text-muted-foreground truncate">Agent</p>
            </div>
          </div>
        </div>
      </aside>

      {/* Main content */}
      <div className="flex-1 flex flex-col min-w-0">
        {/* Mobile header */}
        <header className="lg:hidden h-16 border-b border-border bg-card flex items-center justify-between px-4 shrink-0">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-lg bg-primary flex items-center justify-center">
              <Headphones className="w-5 h-5 text-primary-foreground" />
            </div>
            <h1 className="font-semibold text-lg">InsureFlow</h1>
          </div>
          <button
            onClick={() => setSidebarOpen(true)}
            className="p-2 rounded-lg hover:bg-muted"
            aria-label="Open menu"
          >
            <Menu className="w-5 h-5" />
          </button>
        </header>

        <main className="flex-1 overflow-y-auto p-4 lg:p-8">
          {children}
        </main>
      </div>
    </div>
  );
}