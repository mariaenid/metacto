import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider } from "@metacto/features";
import { Stack } from "expo-router";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1 } },
});

export default function RootLayout() {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Stack screenOptions={{ headerShown: false }} />
      </AuthProvider>
    </QueryClientProvider>
  );
}
