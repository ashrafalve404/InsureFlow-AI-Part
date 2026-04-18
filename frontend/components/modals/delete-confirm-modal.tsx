"use client";

import { useEffect, useState } from "react";
import { AlertTriangle, X } from "lucide-react";
import { cn } from "@/lib/utils";

interface DeleteConfirmModalProps {
  isOpen: boolean;
  onClose: () => void;
  onConfirm: () => void;
  title?: string;
  description?: string;
  loading?: boolean;
}

export function DeleteConfirmModal({
  isOpen,
  onClose,
  onConfirm,
  title = "Delete Call Session",
  description = "Are you sure you want to delete this session? This action cannot be undone and all data will be lost.",
  loading = false,
}: DeleteConfirmModalProps) {
  const [mounted, setMounted] = useState(false);

  useEffect(() => {
    setMounted(true);
  }, []);

  if (!mounted || !isOpen) return null;

  return (
    <div className="fixed inset-0 z-50 flex items-center justify-center p-4 sm:p-6 drop-shadow-2xl">
      {/* Backdrop */}
      <div 
        className="absolute inset-0 bg-background/80 backdrop-blur-sm animate-in fade-in transition-opacity"
        onClick={onClose}
      />
      
      {/* Modal Content */}
      <div className="relative w-full max-w-md bg-card border border-border rounded-2xl shadow-2xl overflow-hidden animate-in zoom-in-95 duration-200">
        <div className="p-6">
          <div className="flex items-center justify-between mb-4">
            <div className="w-10 h-10 rounded-full bg-red-500/10 flex items-center justify-center">
              <AlertTriangle className="w-5 h-5 text-red-500" />
            </div>
            <button 
              onClick={onClose}
              className="text-muted-foreground hover:text-foreground transition-colors p-1"
            >
              <X className="w-5 h-5" />
            </button>
          </div>
          
          <h3 className="text-xl font-semibold mb-2">{title}</h3>
          <p className="text-muted-foreground text-sm leading-relaxed">
            {description}
          </p>
        </div>
        
        <div className="bg-muted/30 p-4 flex flex-col sm:flex-row gap-3 justify-end items-center">
          <button
            onClick={onClose}
            disabled={loading}
            className="w-full sm:w-auto px-4 py-2 text-sm font-medium hover:bg-muted rounded-xl transition-colors disabled:opacity-50"
          >
            Cancel
          </button>
          <button
            onClick={onConfirm}
            disabled={loading}
            className={cn(
              "w-full sm:w-auto px-6 py-2 text-sm font-medium rounded-xl transition-all shadow-lg shadow-red-500/20",
              "bg-red-500 text-white hover:bg-red-600 active:scale-95 disabled:opacity-50"
            )}
          >
            {loading ? "Deleting..." : "Delete Permanently"}
          </button>
        </div>
      </div>
    </div>
  );
}
