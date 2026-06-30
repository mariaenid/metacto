import { DetailScreen } from "@metacto/features";
import { useLocalSearchParams, useRouter } from "expo-router";

export default function RequestDetailScreen() {
  const { id } = useLocalSearchParams<{ id: string }>();
  const router = useRouter();
  return (
    <DetailScreen
      id={id}
      onBack={() => router.back()}
      onAuthRequired={() => router.push("/auth")}
    />
  );
}
