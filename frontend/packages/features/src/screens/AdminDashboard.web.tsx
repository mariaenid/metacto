"use client";

import type { AdminStats, TopRequest } from "@metacto/api-client";
import { useAdminStats } from "../hooks/useAdminStats";

const STATUS_ORDER = [
  "open",
  "under_review",
  "planned",
  "in_progress",
  "shipped",
  "closed",
  "duplicate",
];

const STATUS_STYLES: Record<string, { bg: string; text: string; dot: string }> = {
  open:         { bg: "bg-indigo-50",   text: "text-indigo-700",  dot: "bg-indigo-400" },
  under_review: { bg: "bg-amber-50",    text: "text-amber-700",   dot: "bg-amber-400" },
  planned:      { bg: "bg-emerald-50",  text: "text-emerald-700", dot: "bg-emerald-400" },
  in_progress:  { bg: "bg-blue-50",     text: "text-blue-700",    dot: "bg-blue-400" },
  shipped:      { bg: "bg-emerald-100", text: "text-emerald-800", dot: "bg-emerald-600" },
  closed:       { bg: "bg-red-50",      text: "text-red-700",     dot: "bg-red-400" },
  duplicate:    { bg: "bg-gray-100",    text: "text-gray-500",    dot: "bg-gray-400" },
};

function StatCard({ label, value, sub }: { label: string; value: number | string; sub?: string }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
      <p className="text-sm text-gray-500 font-medium">{label}</p>
      <p className="text-3xl font-bold text-gray-900 mt-1">{value}</p>
      {sub && <p className="text-xs text-gray-400 mt-1">{sub}</p>}
    </div>
  );
}

function StatusBreakdown({ counts }: { counts: Record<string, number> }) {
  const total = Object.values(counts).reduce((a, b) => a + b, 0);
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
      <p className="text-sm font-semibold text-gray-700 mb-4">Requests by status</p>
      <div className="space-y-2.5">
        {STATUS_ORDER.filter((s) => counts[s] !== undefined).map((status) => {
          const count = counts[status] ?? 0;
          const pct = total > 0 ? Math.round((count / total) * 100) : 0;
          const style = STATUS_STYLES[status] ?? STATUS_STYLES.open;
          return (
            <div key={status} className="flex items-center gap-3">
              <span className={`inline-block w-2 h-2 rounded-full flex-shrink-0 ${style.dot}`} />
              <span className="text-sm text-gray-600 w-28 capitalize">{status.replace(/_/g, " ")}</span>
              <div className="flex-1 bg-gray-100 rounded-full h-1.5 overflow-hidden">
                <div
                  className={`h-full rounded-full ${style.dot}`}
                  style={{ width: `${pct}%` }}
                />
              </div>
              <span className="text-sm font-medium text-gray-700 w-8 text-right">{count}</span>
            </div>
          );
        })}
      </div>
    </div>
  );
}

function TopVotedList({ items }: { items: TopRequest[] }) {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
      <p className="text-sm font-semibold text-gray-700 mb-4">Top voted (active)</p>
      {items.length === 0 ? (
        <p className="text-sm text-gray-400">No active requests.</p>
      ) : (
        <ol className="space-y-2">
          {items.map((item, i) => {
            const style = STATUS_STYLES[item.status] ?? STATUS_STYLES.open;
            return (
              <li key={item.id} className="flex items-center gap-3">
                <span className="text-sm font-bold text-gray-300 w-5 text-right">{i + 1}</span>
                <span className="flex-1 text-sm text-gray-700 truncate">{item.title}</span>
                <span className={`text-xs px-2 py-0.5 rounded-full font-medium ${style.bg} ${style.text}`}>
                  {item.status.replace(/_/g, " ")}
                </span>
                <span className="text-sm font-semibold text-gray-900 w-10 text-right">
                  ▲ {item.vote_count}
                </span>
              </li>
            );
          })}
        </ol>
      )}
    </div>
  );
}

function TriageCard({ triage }: { stats: AdminStats; triage: AdminStats["triage"] }) {
  const oldestDate = triage.oldest_open_at
    ? new Date(triage.oldest_open_at).toLocaleDateString("en-US", {
        month: "short",
        day: "numeric",
        year: "numeric",
      })
    : null;

  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5">
      <p className="text-sm font-semibold text-gray-700 mb-4">Triage</p>
      <div className="space-y-3">
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">Oldest open request</span>
          <span className="text-sm font-medium text-gray-900">
            {oldestDate ?? <span className="text-gray-400">—</span>}
          </span>
        </div>
        <div className="flex justify-between items-center">
          <span className="text-sm text-gray-500">Stale under review</span>
          <span
            className={`text-sm font-semibold ${triage.stale_under_review_count > 0 ? "text-amber-600" : "text-gray-400"}`}
          >
            {triage.stale_under_review_count}
          </span>
        </div>
      </div>
    </div>
  );
}

function SkeletonCard() {
  return (
    <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-5 animate-pulse">
      <div className="h-3 bg-gray-200 rounded w-1/3 mb-3" />
      <div className="h-8 bg-gray-100 rounded w-1/2" />
    </div>
  );
}

interface AdminDashboardProps {
  token: string | null;
}

export function AdminDashboard({ token }: AdminDashboardProps) {
  const { data, isLoading, isError, refetch } = useAdminStats(token);

  if (isError) {
    return (
      <div className="text-center py-20 space-y-3">
        <p className="text-gray-500">Failed to load stats.</p>
        <button onClick={() => refetch()} className="text-sm text-indigo-600 hover:underline">
          Try again
        </button>
      </div>
    );
  }

  return (
    <div>
      <div className="mb-8">
        <h1 className="text-2xl font-bold text-gray-900">Admin Dashboard</h1>
        <p className="text-sm text-gray-500 mt-1">Platform health at a glance</p>
      </div>

      {/* Activity last 30 days */}
      <section className="mb-6">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Last 30 days
        </h2>
        <div className="grid grid-cols-3 gap-4">
          {isLoading ? (
            <>
              <SkeletonCard />
              <SkeletonCard />
              <SkeletonCard />
            </>
          ) : (
            <>
              <StatCard label="Submissions" value={data!.activity_30d.submissions} />
              <StatCard label="Votes cast" value={data!.activity_30d.votes} />
              <StatCard label="Status changes" value={data!.activity_30d.transitions} />
            </>
          )}
        </div>
      </section>

      {/* Status breakdown + triage */}
      <section className="mb-6">
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Pipeline
        </h2>
        <div className="grid grid-cols-2 gap-4">
          {isLoading ? (
            <>
              <SkeletonCard />
              <SkeletonCard />
            </>
          ) : (
            <>
              <StatusBreakdown counts={data!.counts_by_status} />
              <TriageCard stats={data!} triage={data!.triage} />
            </>
          )}
        </div>
      </section>

      {/* Top voted */}
      <section>
        <h2 className="text-xs font-semibold text-gray-400 uppercase tracking-wider mb-3">
          Top voted
        </h2>
        {isLoading ? <SkeletonCard /> : <TopVotedList items={data!.top_voted} />}
      </section>
    </div>
  );
}
