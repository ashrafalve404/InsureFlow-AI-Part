"use client";

import { useThemeEffect } from "@/lib/store/theme-store";

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  useThemeEffect();
  return <>{children}</>;
}