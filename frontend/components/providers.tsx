"use client";

import { useEffect } from "react";

export function Providers({ children }: { children: React.ReactNode }) {
  useEffect(() => {
    const root = document.documentElement;
    const stored = localStorage.getItem("theme");
    if (stored === "dark" || (!stored && window.matchMedia("(prefers-color-scheme: dark)").matches)) {
      root.classList.add("dark");
    }
  }, []);

  return <>{children}</>;
}