import { ApiError, type AuthUser, createApiClient } from "@metacto/api-client";
import {
  createContext,
  type ReactNode,
  useCallback,
  useContext,
  useEffect,
  useMemo,
  useState,
} from "react";
import { API_BASE_URL } from "../config";
import { tokenStorage } from "../storage/tokenStorage";

interface AuthState {
  accessToken: string | null;
  user: AuthUser | null;
  isAuthenticated: boolean;
  isHydrated: boolean;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (email: string, displayName: string, password: string) => Promise<void>;
}

const AuthContext = createContext<AuthState | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [accessToken, setAccessToken] = useState<string | null>(null);
  const [user, setUser] = useState<AuthUser | null>(null);
  // Prevents flash of unauthenticated UI while reading persisted token.
  const [isHydrated, setIsHydrated] = useState(false);
  const api = useMemo(() => createApiClient(API_BASE_URL), []);

  const applyTokens = useCallback(
    (access: string, refresh: string) => {
      tokenStorage.set(access, refresh);
      setAccessToken(access);
      api.auth.me(access).then(setUser).catch(() => null);
    },
    [api],
  );

  const clearSession = useCallback(() => {
    tokenStorage.clear();
    setAccessToken(null);
    setUser(null);
  }, []);

  // Attempt silent refresh. Returns new access token or null.
  const tryRefresh = useCallback(async (): Promise<string | null> => {
    const stored = tokenStorage.getRefresh();
    if (!stored) {
      clearSession();
      return null;
    }
    try {
      const { access, refresh } = await api.auth.refresh(stored);
      applyTokens(access, refresh);
      return access;
    } catch {
      clearSession();
      return null;
    }
  }, [api, applyTokens, clearSession]);

  // On mount: restore session from storage, verify token is still valid.
  useEffect(() => {
    const access = tokenStorage.getAccess();
    if (!access) {
      setIsHydrated(true);
      return;
    }
    setAccessToken(access);
    api.auth
      .me(access)
      .then(setUser)
      .catch(async (err) => {
        if (err instanceof ApiError && err.status === 401) {
          await tryRefresh();
        }
      })
      .finally(() => setIsHydrated(true));
  }, [api, tryRefresh]);

  const login = useCallback(
    async (email: string, password: string) => {
      const { access, refresh } = await api.auth.login(email, password);
      applyTokens(access, refresh);
    },
    [api, applyTokens],
  );

  const register = useCallback(
    async (email: string, displayName: string, password: string) => {
      await api.auth.register(email, displayName, password);
    },
    [api],
  );

  const logout = useCallback(() => {
    if (accessToken) api.auth.logout(accessToken).catch(() => null);
    clearSession();
  }, [api, accessToken, clearSession]);

  const value = useMemo(
    () => ({
      accessToken,
      user,
      isAuthenticated: !!accessToken,
      isHydrated,
      login,
      logout,
      register,
    }),
    [accessToken, user, isHydrated, login, logout, register],
  );

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth(): AuthState {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error("useAuth must be used inside AuthProvider");
  return ctx;
}
