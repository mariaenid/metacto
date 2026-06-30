"use client";

import { DetailScreen } from "@metacto/features";
import { useRouter } from "next/navigation";

export default function RequestDetailPage({ params }: { params: { id: string } }) {
  const router = useRouter();
  return (
    <DetailScreen
      id={params.id}
      onBack={() => router.push("/")}
      onAuthRequired={() => router.push("/auth")}
    />
  );
}
