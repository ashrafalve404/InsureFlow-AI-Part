"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { useState } from "react";
import { cn } from "@/lib/utils";
import { Play, Plus, User, Phone, Send } from "lucide-react";

export default function DemoPage() {
  const pathname = "/dashboard/demo";
  const [isActive, setIsActive] = useState(false);
  const [messages, setMessages] = useState<{speaker: string; text: string}[]>([]);
  const [input, setInput] = useState("");

  const startDemo = () => {
    setIsActive(true);
    setMessages([
      { speaker: "agent", text: "Hello, thank you for calling InsureFlow. How can I help you today?" },
      { speaker: "customer", text: "Hi, I'm looking for health insurance for my family." },
    ]);
  };

  const handleSend = (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim()) return;
    setMessages([...messages, { speaker: "agent", text: input }]);
    setInput("");
  };

  return (
    <DashboardLayout pathname={pathname}>
      <div className="max-w-2xl mx-auto">
        <div className="text-center mb-6 lg:mb-8">
          <h1 className="text-xl lg:text-2xl font-semibold mb-2">Demo Mode</h1>
          <p className="text-sm lg:text-base text-muted-foreground">
            Test the AI assistant without connecting to a live backend
          </p>
        </div>

        {!isActive ? (
          <div className="text-center py-12 lg:py-16">
            <div className="w-16 lg:w-20 h-16 lg:h-20 mx-auto mb-4 lg:mb-6 rounded-full bg-primary/10 flex items-center justify-center">
              <Play className="w-8 lg:w-10 h-8 lg:h-10 text-primary" />
            </div>
            <p className="text-muted-foreground mb-4 lg:mb-6">
              Click below to start a demo session
            </p>
            <button
              onClick={startDemo}
              className={cn(
                "inline-flex items-center gap-2 px-6 py-3 rounded-xl",
                "bg-primary text-primary-foreground font-medium",
                "hover:bg-primary/90 transition-colors"
              )}
            >
              <Plus className="w-5 h-5" />
              Start Demo Session
            </button>
          </div>
        ) : (
          <div className="rounded-xl lg:rounded-2xl border border-border bg-card overflow-hidden">
            <div className="p-3 lg:p-4 border-b border-border bg-muted/30">
              <div className="flex items-center justify-between">
                <div className="flex items-center gap-2 lg:gap-3">
                  <div className="w-8 lg:w-10 h-8 lg:h-10 rounded-full bg-primary/10 flex items-center justify-center">
                    <Phone className="w-4 lg:w-5 h-4 lg:h-5 text-primary" />
                  </div>
                  <div>
                    <p className="font-medium text-sm lg:text-base">Demo Call</p>
                    <p className="text-xs text-emerald-600 flex items-center gap-1">
                      <span className="w-2 h-2 rounded-full bg-emerald-600 animate-pulse" />
                      Active
                    </p>
                  </div>
                </div>
                <button
                  onClick={() => { setIsActive(false); setMessages([]); }}
                  className="px-3 lg:px-4 py-2 rounded-xl border border-border text-sm"
                >
                  End Demo
                </button>
              </div>
            </div>

            <div className="p-3 lg:p-4 space-y-3 lg:space-y-4 max-h-[50vh] lg:max-h-96 overflow-y-auto">
              {messages.map((msg, i) => (
                <div
                  key={i}
                  className={cn(
                    "flex flex-col",
                    msg.speaker === "agent" ? "items-end" : "items-start"
                  )}
                >
                  <div className={cn(
                    "max-w-[80%] px-3 lg:px-4 py-2 lg:py-3 rounded-xl lg:rounded-2xl text-sm",
                    msg.speaker === "agent"
                      ? "bg-primary text-primary-foreground rounded-br-md"
                      : "bg-muted rounded-bl-md"
                  )}>
                    {msg.text}
                  </div>
                </div>
              ))}
            </div>

            <form onSubmit={handleSend} className="p-3 lg:p-4 border-t border-border">
              <div className="flex gap-2">
                <input
                  type="text"
                  value={input}
                  onChange={(e) => setInput(e.target.value)}
                  placeholder="Type a transcript message..."
                  className="flex-1 px-3 lg:px-4 py-2 rounded-xl border border-border bg-background text-sm"
                />
                <button 
                  type="submit"
                  className="px-3 lg:px-4 py-2 rounded-xl bg-primary text-primary-foreground"
                >
                  <Send className="w-4 h-4" />
                </button>
              </div>
              <p className="text-xs text-muted-foreground mt-2">
                This sends messages to the AI and simulates the full pipeline
              </p>
            </form>
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}