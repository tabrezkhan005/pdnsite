"use client";

import React from "react";
import { useAuth } from "@/components/AuthProvider";

export default function AdminPortal() {
  const { user, logout } = useAuth();

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card p-4 flex justify-between items-center shadow-sm">
        <h1 className="text-2xl font-heading font-bold text-primary">Admin Dashboard</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">Welcome, Admin {user.last_name}</span>
          <button onClick={logout} className="text-sm font-medium text-destructive hover:underline">
            Logout
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 space-y-6">
        
        <section className="bg-card rounded-xl p-6 border border-border shadow-sm">
          <h2 className="text-xl font-heading font-semibold mb-2">Audit Logs & Overrides</h2>
          <p className="text-muted-foreground mb-6">
            Placeholder view for overriding attendance windows and reviewing system audit logs.
          </p>
          
          <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
            <div className="p-6 rounded-lg border border-border bg-background hover:border-primary/50 transition-colors">
              <h3 className="font-medium text-lg mb-1">Review Audit Logs</h3>
              <p className="text-sm text-muted-foreground mb-4">View detailed trails of all manual edits and attendance overrides.</p>
              <button disabled className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md text-sm opacity-50 cursor-not-allowed">
                Coming Soon
              </button>
            </div>
            
            <div className="p-6 rounded-lg border border-border bg-background hover:border-primary/50 transition-colors">
              <h3 className="font-medium text-lg mb-1">Bypass Edit Windows</h3>
              <p className="text-sm text-muted-foreground mb-4">Edit attendance records older than 48 hours.</p>
              <button disabled className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md text-sm opacity-50 cursor-not-allowed">
                Coming Soon
              </button>
            </div>
          </div>
        </section>

      </main>
    </div>
  );
}
