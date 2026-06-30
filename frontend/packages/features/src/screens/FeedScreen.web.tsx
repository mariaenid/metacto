"use client";

import type { FeatureRequest, SortOption } from "@metacto/api-client";
import { useState } from "react";
import { useFeatureRequests } from "../hooks/useFeatureRequests";

const SORTS: { label: string; value: SortOption }[] = [
  { label: "Top", value: "top" },
  { label: "Hot", value: "hot" },
  { label: "New", value: "new" },
];

const STATUS_STYLES: Record<string, string> = {
  open:         "bg-indigo-50 text-indigo-700",
  under_review: "bg-amber-50 text-amber-700",
  planned:      "bg-emerald-50 text-emerald-700",
  in_progress:  "bg-blue-50 text-blue-700",
  shipped:      "bg-emerald-100 text-emerald-800",
  declined:     "bg-red-50 text-red-700",
  duplicate:    "bg-gray-100 text-gray-500",
};

interface FeedScreenProps {
  onSelectRequest: (id: string) => void;
  onSubmit: () => void;
}

function RequestCard({ item, onClick }: { item: FeatureRequest; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      className="w-full text-left bg-white rounded-xl border border-gray-100 shadow-sm hover:shadow-md hover:border-gray-200 transition-all duration-150 p-5 flex gap-4 items-start group"
    >
      {/* Vote count */}
      <div className="flex-shrink-0 flex flex-col items-center gap-0.5 min-w-[40px]">
        <span className="text-gray-300 group-hover:text-indigo-400 transition-colors text-lg">▲</span>
        <span className="text-lg font-bold text-gray-900 leading-none">{item.vote_count}</span>
      </div>

      {/* Content */}
      <div className="flex-1 min-w-0">
        <p className="font-semibold text-gray-900 truncate group-hover:text-indigo-700 transition-colors">
          {item.title}
        </p>
        {item.description && (
          <p className="text-sm text-gray-500 mt-0.5 line-clamp-2">{item.description}</p>
        )}
        <div className="flex items-center gap-2 mt-2">
          <span
            className={`inline-flex text-xs font-medium px-2 py-0.5 rounded-full ${STATUS_STYLES[item.status] ?? STATUS_STYLES.open}`}
          >
            {item.status.replace(/_/g, " ")}
          </span>
          <span className="text-xs text-gray-400">
            {new Date(item.created_at).toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" })}
          </span>
        </div>
      </div>
    </button>
  );
}

function Skeleton() {
  return (
    <div className="bg-white rounded-xl border border-gray-100 p-5 flex gap-4 animate-pulse">
      <div className="flex flex-col items-center gap-1 min-w-[40px]">
        <div className="h-4 w-4 bg-gray-200 rounded" />
        <div className="h-5 w-6 bg-gray-200 rounded" />
      </div>
      <div className="flex-1 space-y-2">
        <div className="h-4 bg-gray-200 rounded w-2/3" />
        <div className="h-3 bg-gray-100 rounded w-full" />
        <div className="h-3 bg-gray-100 rounded w-1/2" />
      </div>
    </div>
  );
}

export function FeedScreen({ onSelectRequest }: FeedScreenProps) {
  const [sort, setSort] = useState<SortOption>("top");
  const { data, isLoading, isError, refetch } = useFeatureRequests(sort);

  return (
    <div>
      {/* Page header */}
      <div className="mb-6">
        <h1 className="text-2xl font-bold text-gray-900">Feature Requests</h1>
        <p className="text-sm text-gray-500 mt-1">
          {data?.total ?? "—"} requests · vote for the ones you need most
        </p>
      </div>

      {/* Sort tabs */}
      <div className="flex gap-1 mb-6 border-b border-gray-200">
        {SORTS.map((s) => (
          <button
            key={s.value}
            onClick={() => setSort(s.value)}
            className={[
              "px-4 py-2 text-sm font-medium border-b-2 -mb-px transition-colors",
              sort === s.value
                ? "border-indigo-600 text-indigo-600"
                : "border-transparent text-gray-500 hover:text-gray-700",
            ].join(" ")}
          >
            {s.label}
          </button>
        ))}
      </div>

      {/* Content */}
      {isError ? (
        <div className="text-center py-16 space-y-3">
          <p className="text-gray-500">Failed to load requests.</p>
          <button
            onClick={() => refetch()}
            className="text-sm text-indigo-600 hover:underline"
          >
            Try again
          </button>
        </div>
      ) : isLoading ? (
        <div className="space-y-3">
          {Array.from({ length: 5 }).map((_, i) => <Skeleton key={i} />)}
        </div>
      ) : data?.items.length === 0 ? (
        <div className="text-center py-20">
          <p className="text-gray-400 text-lg">No feature requests yet.</p>
          <p className="text-gray-400 text-sm mt-1">Be the first to submit one.</p>
        </div>
      ) : (
        <ul className="space-y-3">
          {data?.items.map((item) => (
            <li key={item.id}>
              <RequestCard item={item} onClick={() => onSelectRequest(item.id)} />
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
