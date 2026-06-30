import { AuthScreen } from "@metacto/features";
import { useRouter } from "expo-router";

export default function AuthPage() {
  const router = useRouter();
  return (
    <AuthScreen
      onSuccess={() => router.push("/")}
      onBack={() => router.back()}
    />
  );
}
