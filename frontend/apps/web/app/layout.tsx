"use client";

import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { AuthProvider, useAuth } from "@metacto/features";
import Link from "next/link";
import type { ReactNode } from "react";
import "./globals.css";

const queryClient = new QueryClient({
  defaultOptions: { queries: { retry: 1, refetchOnWindowFocus: true } },
});

function Navbar() {
  const { isAuthenticated, user, logout } = useAuth();
  return (
    <header className="sticky top-0 z-10 bg-white/80 backdrop-blur border-b border-gray-100">
      <div className="max-w-3xl mx-auto px-4 h-14 flex items-center justify-between">
        <Link href="/" className="font-semibold text-gray-900 tracking-tight">
          metaCTO <span className="text-indigo-600 font-normal">Voting</span>
        </Link>
        <div className="flex items-center gap-2">
          {isAuthenticated ? (
            <>
              {user?.role === "admin" && (
                <Link
                  href="/admin"
                  className="text-sm text-gray-500 hover:text-gray-900 px-3 py-1.5 transition-colors"
                >
                  Dashboard
                </Link>
              )}
              <Link
                href="/submit"
                className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-3 py-1.5 rounded-lg transition-colors"
              >
                + Submit
              </Link>
              <button
                onClick={logout}
                className="text-sm text-gray-500 hover:text-gray-900 px-3 py-1.5 transition-colors"
              >
                Sign out
              </button>
            </>
          ) : (
            <>
              <Link
                href="/submit"
                className="bg-indigo-600 hover:bg-indigo-700 text-white text-sm font-medium px-3 py-1.5 rounded-lg transition-colors"
              >
                + Submit
              </Link>
              <Link
                href="/auth"
                className="text-sm text-gray-600 hover:text-gray-900 px-3 py-1.5 transition-colors"
              >
                Sign in
              </Link>
            </>
          )}
        </div>
      </div>
    </header>
  );
}

function Providers({ children }: { children: ReactNode }) {
  return (
    <QueryClientProvider client={queryClient}>
      <AuthProvider>
        <Navbar />
        <main className="max-w-3xl mx-auto px-4 py-8">{children}</main>
      </AuthProvider>
    </QueryClientProvider>
  );
}

export default function RootLayout({ children }: { children: ReactNode }) {
  return (
    <html lang="en">
      <head>
        <title>metaCTO — Feature Voting</title>
        <meta name="description" content="Submit, discover, and prioritise feature requests." />
      </head>
      <body className="bg-gray-50 min-h-screen antialiased">
        <Providers>{children}</Providers>
      </body>
    </html>
  );
}
