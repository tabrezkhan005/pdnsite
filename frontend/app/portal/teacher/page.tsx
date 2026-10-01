"use client";

import React, { useState } from "react";
import { useAuth } from "@/components/AuthProvider";
import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "@/lib/api";

type Session = {
  id: string;
  batch: string; // The endpoint returns ID or nested object, let's assume it returns a readable string or object
  starts_at: string;
  ends_at: string;
  mode: string;
  status: string;
};

type RosterItem = {
  student_id: string;
  student_name: string;
  status: "PRESENT" | "ABSENT" | "LATE" | "EXCUSED" | null;
  note: string;
};

export default function TeacherPortal() {
  const { user, logout } = useAuth();
  const queryClient = useQueryClient();
  const [selectedSession, setSelectedSession] = useState<Session | null>(null);

  // In a real app we'd pass a date filter.
  const { data: sessions, isLoading: sessionsLoading } = useQuery<Session[]>({
    queryKey: ["teacher-sessions"],
    queryFn: async () => {
      const res = await api.get("/v1/attendance/sessions/");
      return res.data;
    },
  });

  const { data: roster, isLoading: rosterLoading } = useQuery<RosterItem[]>({
    queryKey: ["session-roster", selectedSession?.id],
    queryFn: async () => {
      const res = await api.get(`/v1/attendance/sessions/${selectedSession?.id}/roster/`);
      return res.data;
    },
    enabled: !!selectedSession,
  });

  // Local state for edits
  const [edits, setEdits] = useState<Record<string, RosterItem>>({});

  // Sync edits when roster loads
  React.useEffect(() => {
    if (roster) {
      const initialEdits: Record<string, RosterItem> = {};
      roster.forEach(r => {
        initialEdits[r.student_id] = { ...r };
      });
      // eslint-disable-next-line react-hooks/set-state-in-effect
      setEdits(initialEdits);
    }
  }, [roster]);

  const handleStatusChange = (studentId: string, status: RosterItem["status"]) => {
    setEdits(prev => ({
      ...prev,
      [studentId]: { ...prev[studentId], status }
    }));
  };

  const handleNoteChange = (studentId: string, note: string) => {
    setEdits(prev => ({
      ...prev,
      [studentId]: { ...prev[studentId], note }
    }));
  };

  const submitAttendance = useMutation({
    mutationFn: async () => {
      if (!selectedSession) return;
      const attendances = Object.values(edits).filter(e => e.status !== null);
      await api.post(`/v1/attendance/sessions/${selectedSession.id}/bulk_mark/`, {
        attendances
      });
    },
    onSuccess: () => {
      alert("Attendance marked successfully!");
      queryClient.invalidateQueries({ queryKey: ["session-roster", selectedSession?.id] });
    },
    onError: (err) => {
      // eslint-disable-next-line @typescript-eslint/no-explicit-any
      const error = err as Error & { response?: any };
      alert(error.response?.data?.detail || "Failed to mark attendance.");
    }
  });

  if (!user) return null;

  return (
    <div className="min-h-screen bg-background">
      <header className="border-b border-border bg-card p-4 flex justify-between items-center shadow-sm">
        <h1 className="text-2xl font-heading font-bold text-primary">Teacher Dashboard</h1>
        <div className="flex items-center gap-4">
          <span className="text-sm text-muted-foreground">Welcome, Instructor {user.last_name}</span>
          <button onClick={logout} className="text-sm font-medium text-destructive hover:underline">
            Logout
          </button>
        </div>
      </header>

      <main className="max-w-7xl mx-auto p-6 grid grid-cols-1 lg:grid-cols-3 gap-6">
        
        {/* Sessions List */}
        <div className="lg:col-span-1 space-y-4">
          <h2 className="text-xl font-heading font-semibold">Your Sessions</h2>
          {sessionsLoading ? (
            <p className="text-sm text-muted-foreground">Loading sessions...</p>
          ) : sessions?.length === 0 ? (
            <p className="text-sm text-muted-foreground">No sessions found.</p>
          ) : (
            <div className="space-y-3">
              {sessions?.map(session => (
                <button
                  key={session.id}
                  onClick={() => setSelectedSession(session)}
                  className={`w-full text-left p-4 rounded-xl border transition-all ${
                    selectedSession?.id === session.id 
                      ? "border-primary bg-primary/10 shadow-md" 
                      : "border-border bg-card hover:border-primary/50"
                  }`}
                >
                  <div className="flex justify-between items-start mb-2">
                    <span className="font-medium">Batch Session</span>
                    <span className={`text-xs px-2 py-1 rounded-full ${session.mode === 'ONLINE' ? 'bg-blue-500/20 text-blue-500' : 'bg-green-500/20 text-green-500'}`}>
                      {session.mode}
                    </span>
                  </div>
                  <div className="text-sm text-muted-foreground">
                    {new Date(session.starts_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})} - 
                    {new Date(session.ends_at).toLocaleTimeString([], {hour: '2-digit', minute:'2-digit'})}
                  </div>
                  <div className="mt-2 text-xs font-medium text-primary">Status: {session.status}</div>
                </button>
              ))}
            </div>
          )}
        </div>

        {/* Roster Area */}
        <div className="lg:col-span-2">
          {selectedSession ? (
            <div className="bg-card rounded-xl border border-border shadow-sm flex flex-col h-[calc(100vh-120px)]">
              <div className="p-4 border-b border-border flex justify-between items-center">
                <h2 className="text-xl font-heading font-semibold">Class Roster</h2>
                <button 
                  onClick={() => submitAttendance.mutate()}
                  disabled={submitAttendance.isPending}
                  className="px-4 py-2 bg-primary text-primary-foreground rounded-md font-medium hover:bg-primary/90 disabled:opacity-50 transition-colors"
                >
                  {submitAttendance.isPending ? "Saving..." : "Save Attendance"}
                </button>
              </div>
              
              <div className="p-4 flex-1 overflow-auto">
                {rosterLoading ? (
                  <p className="text-sm text-muted-foreground">Loading roster...</p>
                ) : roster?.length === 0 ? (
                  <p className="text-sm text-muted-foreground">No students enrolled.</p>
                ) : (
                  <div className="space-y-4">
                    {roster?.map(student => {
                      const editState = edits[student.student_id];
                      if (!editState) return null;
                      
                      return (
                        <div key={student.student_id} className="p-4 rounded-lg border border-border bg-background flex flex-col sm:flex-row gap-4 items-center justify-between">
                          <div className="font-medium min-w-[150px]">{student.student_name}</div>
                          
                          <div className="flex gap-2">
                            {(["PRESENT", "LATE", "ABSENT", "EXCUSED"] as const).map(status => (
                              <button
                                key={status}
                                onClick={() => handleStatusChange(student.student_id, status)}
                                className={`px-3 py-1.5 text-xs font-medium rounded-full border transition-colors ${
                                  editState.status === status
                                    ? status === "PRESENT" ? "bg-green-500/20 text-green-600 border-green-500/50"
                                      : status === "LATE" ? "bg-yellow-500/20 text-yellow-600 border-yellow-500/50"
                                      : status === "ABSENT" ? "bg-red-500/20 text-red-600 border-red-500/50"
                                      : "bg-blue-500/20 text-blue-600 border-blue-500/50"
                                    : "bg-background text-muted-foreground border-border hover:bg-accent"
                                }`}
                              >
                                {status}
                              </button>
                            ))}
                          </div>
                          
                          <input
                            type="text"
                            placeholder="Add note..."
                            value={editState.note || ""}
                            onChange={(e) => handleNoteChange(student.student_id, e.target.value)}
                            className="text-sm rounded border border-input bg-background px-2 py-1.5 focus:outline-none focus:ring-1 focus:ring-primary w-full sm:w-auto"
                          />
                        </div>
                      );
                    })}
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="bg-card rounded-xl border border-border shadow-sm h-64 flex items-center justify-center text-muted-foreground">
              Select a session to mark attendance
            </div>
          )}
        </div>

      </main>
    </div>
  );
}
