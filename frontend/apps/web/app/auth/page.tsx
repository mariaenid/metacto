"use client";

import { AuthScreen } from "@metacto/features";
import { useRouter } from "next/navigation";

export default function AuthPage() {
  const router = useRouter();
  return (
    <AuthScreen
      onSuccess={() => router.push("/")}
      onBack={() => router.back()}
    />
  );
}
