import { SubmitScreen } from "@metacto/features";
import { useRouter } from "expo-router";

export default function SubmitPage() {
  const router = useRouter();
  return (
    <SubmitScreen
      onSuccess={() => router.push("/")}
      onBack={() => router.back()}
      onAuthRequired={() => router.push("/auth")}
    />
  );
}
