"use client";

import { FeedScreen } from "@metacto/features";
import { useRouter } from "next/navigation";

export default function HomePage() {
  const router = useRouter();
  return (
    <FeedScreen
      onSelectRequest={(id) => router.push(`/requests/${id}`)}
      onSubmit={() => router.push("/submit")}
      onAuthRequired={() => router.push("/auth")}
    />
  );
}
