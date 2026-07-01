import { ApiError, createApiClient } from "@metacto/api-client";
import type { FeatureRequest, ListPage, SortOption } from "@metacto/api-client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
import { API_BASE_URL } from "../config";

const keys = {
  lists: () => ["feature-requests", "list"] as const,
  // auth flag in key forces a refetch when the user logs in/out
  list: (sort: SortOption, authed: boolean) => ["feature-requests", "list", sort, authed] as const,
  detail: (id: string, authed: boolean) => ["feature-requests", "detail", id, authed] as const,
};

export function useFeatureRequests(sort: SortOption = "top", token?: string | null) {
  const api = useMemo(() => createApiClient(API_BASE_URL), []);
  const authed = !!token;
  return useQuery<ListPage<FeatureRequest>>({
    queryKey: keys.list(sort, authed),
    queryFn: () => api.featureRequests.list({ sort, limit: 20, offset: 0 }, token ?? undefined),
    staleTime: 30_000,
  });
}

export function useFeatureRequest(id: string, token?: string | null) {
  const api = useMemo(() => createApiClient(API_BASE_URL), []);
  const authed = !!token;
  return useQuery<FeatureRequest>({
    queryKey: keys.detail(id, authed),
    queryFn: () => api.featureRequests.get(id, token ?? undefined),
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
      qc.invalidateQueries({ queryKey: keys.lists() });
    },
  });
}

export function useVote(token: string | null, onAuthError?: () => void) {
  const api = useMemo(() => createApiClient(API_BASE_URL), []);
  const qc = useQueryClient();
  const authed = !!token;

  return useMutation({
    mutationFn: ({ id, hasVoted }: { id: string; hasVoted: boolean }) => {
      if (!token) throw new Error("Not authenticated");
      return hasVoted
        ? api.featureRequests.retractVote(id, token)
        : api.featureRequests.castVote(id, token);
    },
    onMutate: async ({ id, hasVoted }) => {
      await qc.cancelQueries({ queryKey: ["feature-requests"] });

      const prevDetail = qc.getQueryData<FeatureRequest>(keys.detail(id, authed));
      if (prevDetail) {
        qc.setQueryData<FeatureRequest>(keys.detail(id, authed), {
          ...prevDetail,
          viewer_has_voted: !hasVoted,
          vote_count: prevDetail.vote_count + (hasVoted ? -1 : 1),
        });
      }

      const listQueries = qc.getQueriesData<ListPage<FeatureRequest>>({ queryKey: keys.lists() });
      const prevLists = listQueries.map(([qk, data]) => ({ qk, data }));
      for (const { qk, data } of prevLists) {
        if (!data) continue;
        qc.setQueryData<ListPage<FeatureRequest>>(qk, {
          ...data,
          items: data.items.map((item) =>
            item.id === id
              ? {
                  ...item,
                  viewer_has_voted: !hasVoted,
                  vote_count: item.vote_count + (hasVoted ? -1 : 1),
                }
              : item,
          ),
        });
      }

      return { prevDetail, prevLists };
    },
    onError: (_err, { id }, ctx) => {
      if (ctx?.prevDetail) qc.setQueryData(keys.detail(id, authed), ctx.prevDetail);
      for (const { qk, data } of ctx?.prevLists ?? []) {
        qc.setQueryData(qk, data);
      }
      if (_err instanceof ApiError && _err.status === 401) {
        onAuthError?.();
      }
    },
    onSettled: (_data, _err, { id }) => {
      qc.invalidateQueries({ queryKey: keys.detail(id, authed) });
      qc.invalidateQueries({ queryKey: keys.lists() });
    },
  });
}

export function useTransitionStatus(token: string | null) {
  const api = useMemo(() => createApiClient(API_BASE_URL), []);
  const qc = useQueryClient();
  const authed = !!token;

  return useMutation({
    mutationFn: ({
      id,
      expectedFrom,
      toStatus,
      reason,
      duplicateOfId,
    }: {
      id: string;
      expectedFrom: string;
      toStatus: string;
      reason?: string;
      duplicateOfId?: string;
    }) => {
      if (!token) throw new Error("Not authenticated");
      return api.featureRequests.transitionStatus(id, { expectedFrom, toStatus, reason, duplicateOfId }, token);
    },
    onSuccess: (_data, { id }) => {
      qc.invalidateQueries({ queryKey: keys.detail(id, authed) });
      qc.invalidateQueries({ queryKey: keys.lists() });
    },
  });
}
