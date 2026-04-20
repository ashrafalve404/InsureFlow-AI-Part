"use client";

import { useEffect, useState } from "react";
import { useRouter, usePathname } from "next/navigation";
import { DashboardLayout as LayoutUI } from "@/components/layout/dashboard-layout";

export default function DashboardLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const router = useRouter();
  const pathname = usePathname();
  const [isAuthorized, setIsAuthorized] = useState(false);

  useEffect(() => {
    // Client-side authentication check
    const auth = localStorage.getItem("isLoggedIn");
    
    if (auth !== "true") {
      router.push("/login");
    } else {
      setIsAuthorized(true);
    }
  }, [router]);

  // Prevent flicker of protected content before redirect
  if (!isAuthorized) {
    return (
      <div className="min-h-screen bg-[#0a0a0b] flex items-center justify-center">
        <div className="flex flex-col items-center gap-4">
          <div className="w-12 h-12 border-4 border-primary/30 border-t-primary rounded-full animate-spin" />
          <p className="text-white/50 text-sm font-medium animate-pulse">Authenticating Session...</p>
        </div>
      </div>
    );
  }

  return (
    <LayoutUI pathname={pathname}>
      {children}
    </LayoutUI>
  );
}
