"use client";

import { AdminDashboard, useAuth } from "@metacto/features";
import { useRouter } from "next/navigation";
import { useEffect } from "react";

export default function AdminPage() {
  const { accessToken, user, isHydrated } = useAuth();
  const router = useRouter();

  useEffect(() => {
    if (!isHydrated) return;
    if (!accessToken || user?.role !== "admin") {
      router.replace("/");
    }
  }, [isHydrated, accessToken, user, router]);

  if (!isHydrated || !accessToken || user?.role !== "admin") {
    return null;
  }

  return <AdminDashboard token={accessToken} />;
}
