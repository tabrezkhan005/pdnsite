"use client";

import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { useAuth } from "@/components/AuthProvider";

export default function PortalIndex() {
  const { user, isLoading } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (isLoading) return;
    
    if (!user) {
      router.replace("/login");
      return;
    }

    if (user.role === "STUDENT") {
      router.replace("/portal/student");
    } else if (user.role === "STAFF") {
      router.replace("/portal/teacher");
    } else if (user.role === "ADMIN") {
      router.replace("/portal/admin");
    } else {
      router.replace("/");
    }
  }, [user, isLoading, router]);

  return (
    <div className="flex min-h-screen items-center justify-center">
      <div className="h-8 w-8 animate-spin rounded-full border-4 border-primary border-t-transparent"></div>
    </div>
  );
}
