"use client";

import { useEffect, useState } from "react";
import { DashboardLayout } from "@/components/layout/dashboard-layout";
import { getSettings, updateSettings } from "@/lib/api";
import { Settings, Save, PhoneCall, Loader2 } from "lucide-react";
import { cn } from "@/lib/utils";

export default function SettingsPage() {
  const pathname = "/dashboard/settings";
  const [loading, setLoading] = useState(true);
  const [saving, setSaving] = useState(false);
  const [saveSuccess, setSaveSuccess] = useState(false);
  
  const [salesNumber, setSalesNumber] = useState("");

  useEffect(() => {
    async function fetchSettings() {
      try {
        const data = await getSettings();
        if (data.settings.SALES_PERSON_NUMBER) {
          setSalesNumber(data.settings.SALES_PERSON_NUMBER);
        } else {
          // Default fallback if not set
          setSalesNumber("+8801723343865");
        }
      } catch (error) {
        console.error("Failed to fetch settings:", error);
      } finally {
        setLoading(false);
      }
    }
    fetchSettings();
  }, []);

  const handleSave = async () => {
    setSaving(true);
    setSaveSuccess(false);
    try {
      await updateSettings({
        SALES_PERSON_NUMBER: salesNumber,
      });
      setSaveSuccess(true);
      setTimeout(() => setSaveSuccess(false), 3000);
    } catch (error) {
      console.error("Failed to save settings:", error);
      alert("Failed to save settings. Check console.");
    } finally {
      setSaving(false);
    }
  };

  return (
    <DashboardLayout pathname={pathname}>
      <div className="max-w-4xl mx-auto py-6 lg:py-8 px-4">
        <div className="mb-8">
          <h1 className="text-2xl font-semibold flex items-center gap-2">
            <Settings className="w-6 h-6 text-primary" />
            System Settings
          </h1>
          <p className="text-muted-foreground mt-1 text-sm lg:text-base">
            Configure application variables, telephony integrations, and agent numbers.
          </p>
        </div>

        {loading ? (
          <div className="flex items-center justify-center py-20">
            <Loader2 className="w-8 h-8 animate-spin text-primary/50" />
          </div>
        ) : (
          <div className="space-y-6">
            {/* Telephony Settings Section */}
            <div className="rounded-2xl border border-border bg-card overflow-hidden">
              <div className="p-4 lg:p-6 border-b border-border bg-muted/30">
                <h2 className="text-lg font-semibold flex items-center gap-2">
                  <PhoneCall className="w-5 h-5 text-primary" />
                  Telephony & Routing
                </h2>
                <p className="text-sm text-muted-foreground">Configure where inbound Twilio calls are routed.</p>
              </div>

              <div className="p-4 lg:p-6 space-y-6">
                <div className="grid gap-2">
                  <label htmlFor="salesNumber" className="text-sm font-medium">
                    Sales Person Destination Number
                  </label>
                  <p className="text-xs text-muted-foreground mb-1">
                    When a customer calls the Twilio number, Twilio will instantly bridge the call to this exact phone number. MUST include country code (e.g., +88...).
                  </p>
                  <input
                    id="salesNumber"
                    type="text"
                    value={salesNumber}
                    onChange={(e) => setSalesNumber(e.target.value)}
                    placeholder="+1234567890"
                    className="flex h-10 w-full lg:max-w-md rounded-md border border-input bg-background px-3 py-2 text-sm ring-offset-background file:border-0 file:bg-transparent file:text-sm file:font-medium placeholder:text-muted-foreground focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-ring focus-visible:ring-offset-2 disabled:cursor-not-allowed disabled:opacity-50"
                  />
                </div>
              </div>
              
              <div className="p-4 lg:p-6 border-t border-border bg-muted/10 flex items-center justify-between">
                <div>
                  {saveSuccess && (
                    <span className="text-sm text-emerald-600 font-medium animate-in fade-in">
                      Successfully saved!
                    </span>
                  )}
                </div>
                <button
                  onClick={handleSave}
                  disabled={saving}
                  className={cn(
                    "inline-flex items-center justify-center gap-2 rounded-xl text-sm font-medium transition-colors focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50",
                    "bg-primary text-primary-foreground hover:bg-primary/90 h-10 px-6 py-2"
                  )}
                >
                  {saving ? (
                    <Loader2 className="w-4 h-4 animate-spin" />
                  ) : (
                    <Save className="w-4 h-4" />
                  )}
                  Save Changes
                </button>
              </div>
            </div>
            
          </div>
        )}
      </div>
    </DashboardLayout>
  );
}