import { createApiClient } from "@metacto/api-client";
import type { FeatureRequest, ListPage, SortOption } from "@metacto/api-client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
import { API_BASE_URL } from "../config";

const keys = {
  list: (sort: SortOption) => ["feature-requests", sort] as const,
  detail: (id: string) => ["feature-requests", id] as const,
};

export function useFeatureRequests(sort: SortOption = "top") {
  const api = useMemo(() => createApiClient(API_BASE_URL), []);
  return useQuery<ListPage<FeatureRequest>>({
    queryKey: keys.list(sort),
    queryFn: () => api.featureRequests.list({ sort, limit: 20, offset: 0 }),
    staleTime: 30_000,
  });
}

export function useFeatureRequest(id: string) {
  const api = useMemo(() => createApiClient(API_BASE_URL), []);
  return useQuery<FeatureRequest>({
    queryKey: keys.detail(id),
    queryFn: () => api.featureRequests.get(id),
    staleTime: 30_000,
    enabled: !!id,
  });
}

export function useSubmitFeatureRequest(token: string | null) {
  const api = useMemo(() => createApiClient(API_BASE_URL), []);
  const qc = useQueryClient();
  return useMutation({
    mutationFn: ({ title, description }: { title: string; description: string }) => {
      if (!token) throw new Error("Not authenticated");
      return api.featureRequests.submit(title, description, token);
    },
    onSuccess: () => {
      // Invalidate all list sorts so the new item appears everywhere.
      qc.invalidateQueries({ queryKey: ["feature-requests"] });
    },
  });
}

export function useVote(token: string | null) {
  const api = useMemo(() => createApiClient(API_BASE_URL), []);
  const qc = useQueryClient();

  return useMutation({
    mutationFn: ({ id, hasVoted }: { id: string; hasVoted: boolean }) => {
      if (!token) throw new Error("Not authenticated");
      return hasVoted
        ? api.featureRequests.retractVote(id, token)
        : api.featureRequests.castVote(id, token);
    },
    onMutate: async ({ id, hasVoted }) => {
      // Optimistic update — flip state immediately.
      await qc.cancelQueries({ queryKey: keys.detail(id) });
      const prev = qc.getQueryData<FeatureRequest>(keys.detail(id));
      if (prev) {
        qc.setQueryData<FeatureRequest>(keys.detail(id), {
          ...prev,
          viewer_has_voted: !hasVoted,
          vote_count: prev.vote_count + (hasVoted ? -1 : 1),
        });
      }
      return { prev };
    },
    onError: (_err, { id }, ctx) => {
      if (ctx?.prev) qc.setQueryData(keys.detail(id), ctx.prev);
    },
    onSettled: (_data, _err, { id }) => {
      qc.invalidateQueries({ queryKey: keys.detail(id) });
    },
  });
}
