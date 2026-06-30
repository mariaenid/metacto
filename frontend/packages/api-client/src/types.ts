/** Domain types mirroring the DRF backend response shapes. */

export type SortOption = "top" | "hot" | "new";

export type FeatureRequestStatus =
  | "open"
  | "under_review"
  | "planned"
  | "in_progress"
  | "shipped"
  | "declined"
  | "duplicate";

export interface FeatureRequest {
  id: string;
  title: string;
  description: string;
  status: FeatureRequestStatus;
  vote_count: number;
  author_id: string;
  viewer_has_voted: boolean;
  created_at: string;
  updated_at: string;
}

export interface ListPage<T> {
  items: T[];
  total: number;
  limit: number;
  offset: number;
}

export interface Comment {
  id: string;
  body: string;
  author_id: string;
  is_deleted: boolean;
  is_hidden: boolean;
  created_at: string;
  updated_at: string;
}

export interface StatusChangeLog {
  id: string;
  from_status: FeatureRequestStatus;
  to_status: FeatureRequestStatus;
  changed_by_id: string;
  reason: string | null;
  changed_at: string;
}

export type TimelineEntry =
  | ({ type: "comment" } & Comment)
  | ({ type: "status_change" } & StatusChangeLog);

export interface LoginResponse {
  access: string;
}

export interface AuthUser {
  id: string;
  email: string;
  display_name: string;
  role: "user" | "moderator" | "admin";
  email_verified: boolean;
}

export interface ApiError {
  code: string;
  detail: string;
}

export interface TopRequest {
  id: string;
  title: string;
  vote_count: number;
  status: string;
}

export interface AdminStats {
  counts_by_status: Record<string, number>;
  activity_30d: {
    submissions: number;
    votes: number;
    transitions: number;
  };
  triage: {
    oldest_open_at: string | null;
    stale_under_review_count: number;
  };
  top_voted: TopRequest[];
}
