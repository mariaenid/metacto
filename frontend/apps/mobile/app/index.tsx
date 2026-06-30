import { FeedScreen } from "@metacto/features";
import { useRouter } from "expo-router";

export default function HomeScreen() {
  const router = useRouter();
  return (
    <FeedScreen
      onSelectRequest={(id) => router.push(`/requests/${id}`)}
      onSubmit={() => router.push("/submit")}
    />
  );
}
