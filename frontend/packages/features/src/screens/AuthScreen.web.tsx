"use client";

import { useState } from "react";
import { useAuth } from "../context/AuthContext";

type Tab = "login" | "register";

interface AuthScreenProps {
  onSuccess: () => void;
  onBack?: () => void;
}

export function AuthScreen({ onSuccess, onBack }: AuthScreenProps) {
  const [tab, setTab] = useState<Tab>("login");
  const [email, setEmail] = useState("");
  const [displayName, setDisplayName] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");
  const [loading, setLoading] = useState(false);
  const [registered, setRegistered] = useState(false);

  const { login, register } = useAuth();

  const handleLogin = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !password) { setError("Email and password are required."); return; }
    setError(""); setLoading(true);
    try {
      await login(email, password);
      onSuccess();
    } catch (err) {
      setError((err as Error).message ?? "Login failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleRegister = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!email || !displayName || !password) { setError("All fields are required."); return; }
    if (password.length < 8) { setError("Password must be at least 8 characters."); return; }
    setError(""); setLoading(true);
    try {
      await register(email, displayName, password);
      setRegistered(true);
    } catch (err) {
      setError((err as Error).message ?? "Registration failed.");
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="max-w-sm mx-auto mt-8">
      {onBack && (
        <button
          onClick={onBack}
          className="text-sm text-gray-500 hover:text-gray-900 transition-colors mb-6 flex items-center gap-1"
        >
          ← Back
        </button>
      )}

      <div className="text-center mb-8">
        <h1 className="text-2xl font-bold text-gray-900">metaCTO</h1>
        <p className="text-sm text-gray-500 mt-1">Feature Voting</p>
      </div>

      <div className="bg-white rounded-xl border border-gray-100 shadow-sm overflow-hidden">
        {/* Tab bar */}
        <div className="grid grid-cols-2 border-b border-gray-100">
          {(["login", "register"] as Tab[]).map((t) => (
            <button
              key={t}
              onClick={() => { setTab(t); setError(""); setRegistered(false); }}
              className={[
                "py-3 text-sm font-medium capitalize transition-colors",
                tab === t
                  ? "text-indigo-600 border-b-2 border-indigo-600 -mb-px bg-white"
                  : "text-gray-500 hover:text-gray-700",
              ].join(" ")}
            >
              {t}
            </button>
          ))}
        </div>

        <div className="p-6">
          {registered ? (
            <div className="text-center space-y-4 py-4">
              <div className="text-4xl">✉️</div>
              <p className="font-semibold text-gray-900">Check your inbox</p>
              <p className="text-sm text-gray-500">
                We sent a verification link to <strong>{email}</strong>. Click it, then come back to log in.
              </p>
              <button
                onClick={() => { setTab("login"); setRegistered(false); }}
                className="text-sm text-indigo-600 hover:underline"
              >
                Go to login →
              </button>
            </div>
          ) : (
            <form onSubmit={tab === "login" ? handleLogin : handleRegister} className="space-y-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Email</label>
                <input
                  type="email"
                  value={email}
                  onChange={(e) => setEmail(e.target.value)}
                  placeholder="you@example.com"
                  autoComplete="email"
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>

              {tab === "register" && (
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-1">Display name</label>
                  <input
                    type="text"
                    value={displayName}
                    onChange={(e) => setDisplayName(e.target.value)}
                    placeholder="Your name"
                    autoComplete="name"
                    className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                  />
                </div>
              )}

              <div>
                <label className="block text-sm font-medium text-gray-700 mb-1">Password</label>
                <input
                  type="password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  placeholder="••••••••"
                  autoComplete={tab === "login" ? "current-password" : "new-password"}
                  className="w-full border border-gray-200 rounded-lg px-3 py-2 text-sm text-gray-900 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-indigo-500 focus:border-transparent"
                />
              </div>

              {error && (
                <div className="bg-red-50 border border-red-100 rounded-lg px-3 py-2">
                  <p className="text-sm text-red-600">{error}</p>
                </div>
              )}

              <button
                type="submit"
                disabled={loading}
                className="w-full bg-indigo-600 hover:bg-indigo-700 disabled:opacity-50 disabled:cursor-not-allowed text-white font-medium py-2.5 rounded-lg transition-colors text-sm"
              >
                {loading
                  ? "Please wait…"
                  : tab === "login" ? "Sign In" : "Create Account"}
              </button>
            </form>
          )}
        </div>
      </div>
    </div>
  );
}
