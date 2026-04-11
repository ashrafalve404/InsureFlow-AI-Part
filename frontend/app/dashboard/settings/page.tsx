"use client";

import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { Settings } from "lucide-react";

export default function SettingsPage() {
  const pathname = "/dashboard/settings";

  return (
    <DashboardLayout pathname={pathname}>
      <div className="p-8">
        <div className="max-w-2xl mx-auto text-center py-16">
          <div className="w-16 h-16 mx-auto mb-6 rounded-full bg-muted flex items-center justify-center">
            <Settings className="w-8 h-8 text-muted-foreground" />
          </div>
          <h1 className="text-2xl font-semibold mb-2">Settings</h1>
          <p className="text-muted-foreground">
            Coming soon. Configure your AI model, Twilio credentials, and more.
          </p>
        </div>
      </div>
    </DashboardLayout>
  );
}