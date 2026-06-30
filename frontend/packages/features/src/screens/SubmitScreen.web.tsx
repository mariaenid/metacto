"use client";

import { useState } from "react";
import { useAuth } from "../context/AuthContext";
import { useSubmitFeatureRequest } from "../hooks/useFeatureRequests";

interface SubmitScreenProps {
  onSuccess: () => void;
  onBack: () => void;
  onAuthRequired: () => void;
}

export function SubmitScreen({ onSuccess, onBack, onAuthRequired }: SubmitScreenProps) {
  const { accessToken, isAuthenticated } = useAuth();
  const [title, setTitle] = useState("");
  const [description, setDescription] = useState("");
  const [titleError, setTitleError] = useState("");

  const submit = useSubmitFeatureRequest(accessToken);

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    if (!isAuthenticated) { onAuthRequired(); return; }
    if (title.trim().length < 5) {
      setTitleError("Title must be at least 5 characters.");
      return;
    }
    setTitleError("");
    submit.mutate({ title: title.trim(), description: description.trim() }, {
      onSuccess: () => onSuccess(),
    });
  };

  return (
    <div className="max-w-xl mx-auto">
      <button
        onClick={onBack}
        className="text-sm text-gray-500 hover:text-gray-900 transition-colors mb-6 flex items-center gap-1"
      >
        ← Back
      </button>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm p-6">
        <h1 className="text-xl font-bold text-gray-900 mb-1">Submit a Feature Request</h1>
        <p className="text-sm text-gray-500 mb-6">
          Describe the feature and the problem it solves.
        </p>

        <form onSubmit={handleSubmit} className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Title <span className="text-red-400">*</span>
            </label>
            <input
              type="text"
              value={title}
              onChange={(e) => setTitle(e.target.value)}
              placeholder="Describe the feature in one line"
              className={[
                "w-full border rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent",
                titleError ? "border-red-400" : "border-gray-200",
              ].join(" ")}
            />
            {titleError && <p className="text-xs text-red-500 mt-1">{titleError}</p>}
          </div>

          <div>
            <label className="block text-sm font-medium text-gray-700 mb-1">
              Description <span className="text-gray-400 font-normal">(optional)</span>
            </label>
            <textarea
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              placeholder="Explain the problem this solves and any relevant context…"
              rows={5}
              className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent resize-none"
            />
          </div>

          {submit.isError && (
            <div className="bg-red-50 border border-red-100 rounded-lg px-4 py-3">
              <p className="text-sm text-red-600">
                {(submit.error as Error)?.message ?? "Submission failed. Please try again."}
              </p>
            </div>
          )}

          <button
            type="submit"
            disabled={submit.isPending}
            className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg transition-colors text-sm"
          >
            {submit.isPending ? "Submitting…" : "Submit Request"}
          </button>

          {!isAuthenticated && (
            <p className="text-xs text-gray-400 text-center">
              You need to{" "}
              <button
                type="button"
                onClick={onAuthRequired}
                className="text-indigo-600 hover:underline"
              >
                sign in
              </button>{" "}
              with a verified email to submit.
            </p>
          )}
        </form>
      </div>
    </div>
  );
}
