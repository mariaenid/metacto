import { useQuery } from "@tanstack/react-query";
import { createApiClient } from "@metacto/api-client";

const client = createApiClient(process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000");

export function useAdminStats(token: string | null) {
  return useQuery({
    queryKey: ["admin", "stats"],
    queryFn: () => client.admin.getStats(token!),
    enabled: !!token,
    staleTime: 60_000,
  });
}
