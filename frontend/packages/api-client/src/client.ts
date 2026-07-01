import type {
  AdminStats,
  AuthUser,
  Comment,
  FeatureRequest,
  ListPage,
  LoginResponse,
  SortOption,
  TimelineEntry,
} from "./types";

export class ApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: string,
    message: string,
  ) {
    super(message);
    this.name = "ApiError";
  }
}

async function request<T>(
  baseUrl: string,
  path: string,
  options: RequestInit & { token?: string } = {},
): Promise<T> {
  const { token, ...init } = options;
  const headers: Record<string, string> = {
    "Content-Type": "application/json",
    ...(init.headers as Record<string, string>),
  };
  if (token) headers["Authorization"] = `Bearer ${token}`;

  const res = await fetch(`${baseUrl}${path}`, { ...init, headers });
  if (res.status === 204) return undefined as T;

  const body = await res.json().catch(() => ({}));
  if (!res.ok) {
    throw new ApiError(res.status, body.code ?? "unknown", body.detail ?? res.statusText);
  }
  return body as T;
}

export function createApiClient(baseUrl: string) {
  const get = <T>(path: string, token?: string) =>
    request<T>(baseUrl, path, { method: "GET", token });

  const post = <T>(path: string, data?: unknown, token?: string) =>
    request<T>(baseUrl, path, {
      method: "POST",
      body: data !== undefined ? JSON.stringify(data) : undefined,
      token,
    });

  const patch = <T>(path: string, data: unknown, token?: string) =>
    request<T>(baseUrl, path, { method: "PATCH", body: JSON.stringify(data), token });

  const del = (path: string, token?: string) =>
    request<void>(baseUrl, path, { method: "DELETE", token });

  return {
    auth: {
      register: (email: string, displayName: string, password: string) =>
        post<void>("/v1/auth/register", { email, display_name: displayName, password }),

      verifyEmail: (token: string) =>
        post<void>("/v1/auth/verify-email", { token }),

      login: (email: string, password: string) =>
        post<LoginResponse>("/v1/auth/login", { email, password }),

      refresh: (refreshToken: string) =>
        post<LoginResponse>("/v1/auth/refresh", { refresh: refreshToken }),

      logout: (token: string) =>
        post<void>("/v1/auth/logout", undefined, token),

      me: (token: string) =>
        get<AuthUser>("/v1/auth/me", token),
    },

    featureRequests: {
      list: (params: { sort?: SortOption; limit?: number; offset?: number } = {}, token?: string) => {
        const qs = new URLSearchParams();
        if (params.sort) qs.set("sort", params.sort);
        if (params.limit != null) qs.set("limit", String(params.limit));
        if (params.offset != null) qs.set("offset", String(params.offset));
        return get<ListPage<FeatureRequest>>(`/v1/feature-requests?${qs}`, token);
      },

      get: (id: string, token?: string) =>
        get<FeatureRequest>(`/v1/feature-requests/${id}`, token),

      submit: (title: string, description: string, token: string) =>
        post<FeatureRequest>("/v1/feature-requests", { title, description }, token),

      castVote: (id: string, token: string) =>
        post<void>(`/v1/feature-requests/${id}/vote`, undefined, token),

      retractVote: (id: string, token: string) =>
        del(`/v1/feature-requests/${id}/vote`, token),

      transitionStatus: (
        id: string,
        body: { expectedFrom: string; toStatus: string; reason?: string; duplicateOfId?: string },
        token: string,
      ) =>
        patch<{ feature_request: FeatureRequest }>(
          `/v1/feature-requests/${id}/status`,
          {
            expected_from: body.expectedFrom,
            to_status: body.toStatus,
            reason: body.reason ?? null,
            duplicate_of_id: body.duplicateOfId ?? null,
          },
          token,
        ),
    },

    comments: {
      list: (featureRequestId: string, token?: string) =>
        get<ListPage<Comment>>(`/v1/feature-requests/${featureRequestId}/comments`, token),

      post: (featureRequestId: string, body: string, token: string) =>
        post<Comment>(
          `/v1/feature-requests/${featureRequestId}/comments`,
          { body },
          token,
        ),

      edit: (commentId: string, body: string, token: string) =>
        patch<Comment>(`/v1/comments/${commentId}`, { body }, token),

      delete: (commentId: string, token: string) =>
        del(`/v1/comments/${commentId}`, token),

      hide: (commentId: string, token: string) =>
        post<void>(`/v1/comments/${commentId}/hide`, undefined, token),
    },

    timeline: {
      get: (featureRequestId: string, token?: string) =>
        get<ListPage<TimelineEntry>>(
          `/v1/feature-requests/${featureRequestId}/timeline`,
          token,
        ),
    },

    admin: {
      getStats: (token: string) => get<AdminStats>("/v1/admin/stats", token),
    },
  };
}

export type Client = ReturnType<typeof createApiClient>;
