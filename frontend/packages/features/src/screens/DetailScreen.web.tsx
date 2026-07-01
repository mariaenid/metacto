"use client";

import type { Comment } from "@metacto/api-client";
import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useComments, useDeleteComment, useHideComment, usePostComment } from "../hooks/useComments";
import { useFeatureRequest, useTransitionStatus, useVote } from "../hooks/useFeatureRequests";

const STATUS_STYLES: Record<string, string> = {
  open:         "bg-indigo-50 text-indigo-700",
  under_review: "bg-amber-50 text-amber-700",
  planned:      "bg-emerald-50 text-emerald-700",
  in_progress:  "bg-blue-50 text-blue-700",
  shipped:      "bg-emerald-100 text-emerald-800",
  closed:       "bg-red-50 text-red-700",
  duplicate:    "bg-gray-100 text-gray-500",
};

const VALID_TRANSITIONS: Record<string, string[]> = {
  open:         ["under_review", "closed", "duplicate"],
  under_review: ["planned", "closed", "duplicate"],
  planned:      ["in_progress", "closed", "duplicate"],
  in_progress:  ["shipped", "closed", "duplicate"],
  shipped:      [],
  closed:       [],
  duplicate:    [],
};

const STATUS_LABELS: Record<string, string> = {
  under_review: "Under Review",
  planned:      "Planned",
  in_progress:  "In Progress",
  shipped:      "Shipped",
  closed:       "Closed",
  duplicate:    "Duplicate",
};

interface DetailScreenProps {
  id: string;
  onBack: () => void;
  onAuthRequired: () => void;
}

function CommentRow({
  comment,
  canModerate,
  onDelete,
  onHide,
}: {
  comment: Comment;
  canModerate: boolean;
  onDelete: (id: string) => void;
  onHide: (id: string) => void;
}) {
  const isDeleted = comment.is_deleted;
  const isHidden = comment.is_hidden;
  return (
    <div className="py-4 border-b border-gray-100 last:border-0">
      <div className="flex items-center justify-between mb-1">
        <span className="text-xs text-gray-400">
          {new Date(comment.created_at).toLocaleDateString("en-US", {
            month: "short", day: "numeric", year: "numeric",
          })}
        </span>
        {canModerate && !isDeleted && (
          <div className="flex gap-3">
            {!isHidden && (
              <button onClick={() => onHide(comment.id)} className="text-xs text-gray-400 hover:text-amber-500 transition-colors">
                Hide
              </button>
            )}
            <button onClick={() => onDelete(comment.id)} className="text-xs text-gray-400 hover:text-red-500 transition-colors">
              Delete
            </button>
          </div>
        )}
      </div>
      <p className={`text-sm leading-relaxed ${isDeleted || isHidden ? "text-gray-400 italic" : "text-gray-700"}`}>
        {isDeleted ? "Comment deleted." : isHidden ? "Comment hidden by moderator." : comment.body}
      </p>
    </div>
  );
}

function StatusTransitionPanel({
  requestId,
  currentStatus,
  token,
}: {
  requestId: string;
  currentStatus: string;
  token: string;
}) {
  const [toStatus, setToStatus] = useState("");
  const [reason, setReason] = useState("");
  const [duplicateOfId, setDuplicateOfId] = useState("");
  const [error, setError] = useState<string | null>(null);
  const transition = useTransitionStatus(token);
  const options = VALID_TRANSITIONS[currentStatus] ?? [];

  if (options.length === 0) return null;

  const handleSubmit = () => {
    if (!toStatus) return;
    setError(null);
    transition.mutate(
      {
        id: requestId,
        expectedFrom: currentStatus,
        toStatus,
        reason: reason.trim() || undefined,
        duplicateOfId: toStatus === "duplicate" ? duplicateOfId.trim() || undefined : undefined,
      },
      {
        onSuccess: () => {
          setToStatus("");
          setReason("");
          setDuplicateOfId("");
        },
        onError: (err: any) => {
          setError(err?.message ?? "Transition failed");
        },
      },
    );
  };

  return (
    <div className="bg-white rounded-xl border border-amber-100 shadow-sm p-5">
      <p className="text-sm font-semibold text-gray-700 mb-4 flex items-center gap-2">
        <span className="inline-block w-2 h-2 rounded-full bg-amber-400" />
        Moderator actions
      </p>

      <div className="space-y-3">
        <div>
          <label className="text-xs font-medium text-gray-500 mb-1 block">Move to status</label>
          <div className="flex flex-wrap gap-2">
            {options.map((s) => (
              <button
                key={s}
                onClick={() => setToStatus(toStatus === s ? "" : s)}
                className={[
                  "px-3 py-1.5 rounded-lg text-xs font-medium border transition-all",
                  toStatus === s
                    ? "bg-indigo-600 text-white border-indigo-600"
                    : "border-gray-200 text-gray-600 hover:border-indigo-300 hover:text-indigo-600",
                ].join(" ")}
              >
                {STATUS_LABELS[s] ?? s}
              </button>
            ))}
          </div>
        </div>

        {toStatus === "duplicate" && (
          <div>
            <label className="text-xs font-medium text-gray-500 mb-1 block">Original request ID</label>
            <input
              value={duplicateOfId}
              onChange={(e) => setDuplicateOfId(e.target.value)}
              placeholder="UUID of the original request"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        )}

        {toStatus && (
          <div>
            <label className="text-xs font-medium text-gray-500 mb-1 block">Reason <span className="text-gray-400">(optional)</span></label>
            <input
              value={reason}
              onChange={(e) => setReason(e.target.value)}
              placeholder="Explain this transition…"
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-indigo-500"
            />
          </div>
        )}

        {error && <p className="text-xs text-red-500">{error}</p>}

        <button
          onClick={handleSubmit}
          disabled={!toStatus || transition.isPending}
          className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
        >
          {transition.isPending ? "Applying…" : "Apply transition"}
        </button>
      </div>
    </div>
  );
}

export function DetailScreen({ id, onBack, onAuthRequired }: DetailScreenProps) {
  const { accessToken, isAuthenticated, user } = useAuth();
  const [commentBody, setCommentBody] = useState("");
  const isMod = user?.role === "moderator" || user?.role === "admin";

  const { data: fr, isLoading } = useFeatureRequest(id, accessToken);
  const { data: commentsPage, isLoading: cmtLoading } = useComments(id);
  const vote = useVote(accessToken);
  const postComment = usePostComment(id, accessToken);
  const deleteComment = useDeleteComment(id, accessToken);
  const hideComment = useHideComment(id, accessToken);

  if (isLoading) {
    return (
      <div className="animate-pulse space-y-4">
        <div className="h-6 bg-gray-200 rounded w-3/4" />
        <div className="h-4 bg-gray-100 rounded w-full" />
        <div className="h-4 bg-gray-100 rounded w-2/3" />
      </div>
    );
  }

  if (!fr) {
    return (
      <div className="text-center py-20 space-y-3">
        <p className="text-gray-500">Request not found.</p>
        <button onClick={onBack} className="text-sm text-indigo-600 hover:underline">← Back to feed</button>
      </div>
    );
  }

  const handleVote = () => {
    if (!isAuthenticated) { onAuthRequired(); return; }
    vote.mutate({ id: fr.id, hasVoted: fr.viewer_has_voted });
  };

  const handleComment = () => {
    if (!isAuthenticated) { onAuthRequired(); return; }
    if (!commentBody.trim()) return;
    postComment.mutate(commentBody, { onSuccess: () => setCommentBody("") });
  };

  return (
    <div className="space-y-4">
      <button onClick={onBack} className="text-sm text-gray-500 hover:text-gray-900 flex items-center gap-1 transition-colors">
        ← Back
      </button>

      {/* Main card */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <div className="flex items-start gap-4">
          {/* Vote button */}
          <button
            onClick={handleVote}
            disabled={vote.isPending}
            aria-label={fr.viewer_has_voted ? "Remove vote" : "Vote"}
            className={[
              "flex-shrink-0 flex flex-col items-center gap-1 px-3 py-2 rounded-xl border-2 transition-all duration-150 min-w-[56px]",
              fr.viewer_has_voted
                ? "border-indigo-600 bg-indigo-600 text-white"
                : "border-gray-200 hover:border-indigo-400 text-gray-500 hover:text-indigo-600",
            ].join(" ")}
          >
            <span className="text-base leading-none">▲</span>
            <span className="text-lg font-bold leading-none">{fr.vote_count}</span>
          </button>

          <div className="flex-1 min-w-0">
            <div className="flex items-start gap-3 flex-wrap">
              <h1 className="text-xl font-bold text-gray-900 flex-1">{fr.title}</h1>
              <span className={`text-xs font-medium px-2.5 py-1 rounded-full flex-shrink-0 ${STATUS_STYLES[fr.status] ?? STATUS_STYLES.open}`}>
                {fr.status.replace(/_/g, " ")}
              </span>
            </div>
            {fr.description && (
              <p className="text-gray-600 mt-3 text-sm leading-relaxed">{fr.description}</p>
            )}
            <p className="text-xs text-gray-400 mt-3">
              Submitted {new Date(fr.created_at).toLocaleDateString("en-US", { month: "long", day: "numeric", year: "numeric" })}
            </p>
          </div>
        </div>
      </div>

      {/* Moderator panel */}
      {isMod && accessToken && (
        <StatusTransitionPanel
          requestId={fr.id}
          currentStatus={fr.status}
          token={accessToken}
        />
      )}

      {/* Comments */}
      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h2 className="font-semibold text-gray-900 mb-4">
          Comments <span className="text-gray-400 font-normal">({commentsPage?.total ?? 0})</span>
        </h2>

        {cmtLoading ? (
          <div className="space-y-3 animate-pulse">
            {[1, 2].map((i) => <div key={i} className="h-10 bg-gray-100 rounded" />)}
          </div>
        ) : (
          <div>
            {commentsPage?.items.map((c) => (
              <CommentRow
                key={c.id}
                comment={c}
                canModerate={isMod || isAuthenticated}
                onDelete={(cid) => deleteComment.mutate(cid)}
                onHide={(cid) => hideComment.mutate(cid)}
              />
            ))}
            {commentsPage?.items.length === 0 && (
              <p className="text-sm text-gray-400 py-4">No comments yet. Be the first!</p>
            )}
          </div>
        )}

        <div className="mt-4 pt-4 border-t border-gray-100 space-y-2">
          <textarea
            value={commentBody}
            onChange={(e) => setCommentBody(e.target.value)}
            placeholder={isAuthenticated ? "Add a comment…" : "Sign in to comment"}
            disabled={!isAuthenticated}
            rows={3}
            className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none disabled:bg-gray-50 disabled:cursor-not-allowed"
          />
          <button
            onClick={handleComment}
            disabled={!commentBody.trim() || postComment.isPending || !isAuthenticated}
            className="bg-indigo-600 hover:bg-indigo-700 disabled:opacity-40 disabled:cursor-not-allowed text-white text-sm font-medium px-4 py-2 rounded-lg transition-colors"
          >
            {postComment.isPending ? "Posting…" : "Post Comment"}
          </button>
        </div>
      </div>
    </div>
  );
}
