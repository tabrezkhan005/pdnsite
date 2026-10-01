"use client";

import React, { useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { useQuery } from "@tanstack/react-query";
import api from "@/lib/api";

export default function StudentPortal() {
  const { user, logout } = useAuth();
  const [joinError, setJoinError] = useState("");
  const [isJoining, setIsJoining] = useState(false);
  const [leaveReason, setLeaveReason] = useState("");
  const [leaveFrom, setLeaveFrom] = useState("");
  const [leaveTo, setLeaveTo] = useState("");

  const { data: summary, isLoading: summaryLoading } = useQuery({
    queryKey: ["attendance-summary"],
    queryFn: async () => {
      const res = await api.get("/v1/attendance/summary/");
      return res.data;
    },
  });

  // Fallback next session for demonstration
  const [nextSession, setNextSession] = useState<{id: string; batch_name: string; starts_at: string; ends_at: string; is_open: boolean} | null>(null);

  React.useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    setNextSession({
      id: "demo-session-id",
      batch_name: "Kuchipudi Beginner - GNT",
      starts_at: new Date(Date.now() + 5 * 60000).toISOString(),
      ends_at: new Date(Date.now() + 65 * 60000).toISOString(),
      is_open: true,
    });
  }, []);

  const handleJoin = async () => {
    if (!nextSession) return;
    setIsJoining(true);
    setJoinError("");
    try {
      const res = await api.post(`/v1/attendance/sessions/${nextSession.id}/join/`);
      if (res.data.meeting_url) {
        window.open(res.data.meeting_url, "_blank");
      }
    } catch (err) {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const error = err as Error & { response?: any };
      setJoinError(error.response?.data?.detail || "Failed to join session. Please ensure you are within the 10 minute window.");
    } finally {
      setIsJoining(false);
    }
  };

  const handleLeaveSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await api.post("/v1/attendance/leaves/", {
        from_date: leaveFrom,
        to_date: leaveTo,
        reason: leaveReason,
        student: user?.id,
      });
      alert("Leave request submitted successfully.");
      setLeaveReason("");
      setLeaveFrom("");
      setLeaveTo("");
    } catch {
      alert("Failed to submit leave request.");
    }
  };

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card p-4 flex justify-between items-center shadow-sm">
        <h1 className="text-2xl font-heading font-bold text-primary">Student Dashboard</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">Welcome, {user.first_name}</span>
          <button onClick={logout} className="text-sm font-medium text-destructive hover:underline">
            Logout
          </button>
        </div>
      </header>

      <main className="max-w-5xl mx-auto p-6 grid grid-cols-1 md:grid-cols-3 gap-6">
        
        {/* Next Session Card */}
        <div className="md:col-span-2 space-y-6">
          <section className="bg-card rounded-xl p-6 border border-border shadow-sm">
            <h2 className="text-xl font-heading font-semibold mb-4">Next Session</h2>
            {nextSession ? (
              <div className="p-4 bg-primary/10 rounded-lg border border-primary/20 flex flex-col sm:flex-row justify-between items-center gap-4">
                <div>
                  <h3 className="font-medium text-lg">{nextSession.batch_name}</h3>
                  <p className="text-muted-foreground text-sm">
                    {new Date(nextSession.starts_at).toLocaleString()}
                  </p>
                </div>
                <button 
                  onClick={handleJoin}
                  disabled={!nextSession.is_open || isJoining}
                  className="px-6 py-2 bg-primary text-primary-foreground rounded-full font-medium hover:bg-primary/90 disabled:opacity-50 transition-all shadow-md hover:shadow-lg"
                >
                  {isJoining ? "Joining..." : "Join Online Class"}
                </button>
              </div>
            ) : (
              <p className="text-muted-foreground">Loading next session...</p>
            )}
            {joinError && <p className="text-destructive text-sm mt-3">{joinError}</p>}
          </section>

          {/* Leave Request Form */}
          <section className="bg-card rounded-xl p-6 border border-border shadow-sm">
            <h2 className="text-xl font-heading font-semibold mb-4">Request Leave</h2>
            <form onSubmit={handleLeaveSubmit} className="space-y-4">
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-sm font-medium mb-1">From Date</label>
                  <input 
                    type="date" 
                    value={leaveFrom} 
                    onChange={e => setLeaveFrom(e.target.value)}
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium mb-1">To Date</label>
                  <input 
                    type="date" 
                    value={leaveTo} 
                    onChange={e => setLeaveTo(e.target.value)}
                    required
                    className="w-full rounded-md border border-input bg-background px-3 py-2"
                  />
                </div>
              </div>
              <div>
                <label className="block text-sm font-medium mb-1">Reason</label>
                <textarea 
                  value={leaveReason}
                  onChange={e => setLeaveReason(e.target.value)}
                  required
                  className="w-full rounded-md border border-input bg-background px-3 py-2"
                  rows={3}
                ></textarea>
              </div>
              <button type="submit" className="px-4 py-2 bg-secondary text-secondary-foreground rounded-md font-medium hover:bg-secondary/80 transition-colors">
                Submit Request
              </button>
            </form>
          </section>
        </div>

        {/* Attendance Summary */}
        <div className="space-y-6">
          <section className="bg-card rounded-xl p-6 border border-border shadow-sm">
            <h2 className="text-xl font-heading font-semibold mb-4">Attendance</h2>
            {summaryLoading ? (
              <div className="animate-pulse flex space-x-4">
                <div className="flex-1 space-y-4 py-1">
                  <div className="h-4 bg-muted rounded w-3/4"></div>
                  <div className="space-y-2">
                    <div className="h-4 bg-muted rounded"></div>
                    <div className="h-4 bg-muted rounded w-5/6"></div>
                  </div>
                </div>
              </div>
            ) : summary ? (
              <div className="space-y-4">
                <div className="text-center p-6 bg-accent rounded-lg border border-accent-foreground/10">
                  <span className="text-4xl font-bold text-primary">{summary.percentage}%</span>
                  <p className="text-sm text-muted-foreground mt-1">Overall Attendance</p>
                </div>
                <div className="grid grid-cols-2 gap-2 text-sm">
                  <div className="p-3 bg-background rounded border border-border flex justify-between">
                    <span className="text-muted-foreground">Present</span>
                    <span className="font-medium text-green-500">{summary.present}</span>
                  </div>
                  <div className="p-3 bg-background rounded border border-border flex justify-between">
                    <span className="text-muted-foreground">Late</span>
                    <span className="font-medium text-yellow-500">{summary.late}</span>
                  </div>
                  <div className="p-3 bg-background rounded border border-border flex justify-between">
                    <span className="text-muted-foreground">Absent</span>
                    <span className="font-medium text-destructive">{summary.absent}</span>
                  </div>
                  <div className="p-3 bg-background rounded border border-border flex justify-between">
                    <span className="text-muted-foreground">Excused</span>
                    <span className="font-medium text-blue-500">{summary.excused}</span>
                  </div>
                </div>
              </div>
            ) : (
              <p className="text-sm text-muted-foreground">No data available.</p>
            )}
          </section>
        </div>

      </main>
    </div>
  );
}
