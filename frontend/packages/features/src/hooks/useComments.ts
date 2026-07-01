import { createApiClient } from "@metacto/api-client";
import type { Comment, ListPage } from "@metacto/api-client";
import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import { useMemo } from "react";
import { API_BASE_URL } from "../config";

const keys = {
  list: (featureRequestId: string) =>
    ["comments", featureRequestId] as const,
};

export function useComments(featureRequestId: string) {
  const api = useMemo(() => createApiClient(API_BASE_URL), []);
  return useQuery<ListPage<Comment>>({
    queryKey: keys.list(featureRequestId),
    queryFn: () => api.comments.list(featureRequestId),
    staleTime: 15_000,
    enabled: !!featureRequestId,
  });
}

export function usePostComment(featureRequestId: string, token: string | null) {
  const api = useMemo(() => createApiClient(API_BASE_URL), []);
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (body: string) => {
      if (!token) throw new Error("Not authenticated");
      return api.comments.post(featureRequestId, body, token);
    },
    onSuccess: (newComment) => {
      // Append optimistically to cache.
      qc.setQueryData<ListPage<Comment>>(
        keys.list(featureRequestId),
        (prev) =>
          prev
            ? { ...prev, items: [...prev.items, newComment], total: prev.total + 1 }
            : { items: [newComment], total: 1, limit: 20, offset: 0 },
      );
    },
  });
}

export function useDeleteComment(featureRequestId: string, token: string | null) {
  const api = useMemo(() => createApiClient(API_BASE_URL), []);
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (commentId: string) => {
      if (!token) throw new Error("Not authenticated");
      return api.comments.delete(commentId, token);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.list(featureRequestId) });
    },
  });
}

export function useHideComment(featureRequestId: string, token: string | null) {
  const api = useMemo(() => createApiClient(API_BASE_URL), []);
  const qc = useQueryClient();

  return useMutation({
    mutationFn: (commentId: string) => {
      if (!token) throw new Error("Not authenticated");
      return api.comments.hide(commentId, token);
    },
    onSuccess: () => {
      qc.invalidateQueries({ queryKey: keys.list(featureRequestId) });
    },
  });
}
