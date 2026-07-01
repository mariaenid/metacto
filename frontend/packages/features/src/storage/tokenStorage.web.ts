const ACCESS_KEY = "metacto_access_token";
const REFRESH_KEY = "metacto_refresh_token";

function ls(fn: () => string | null): string | null {
  try { return fn(); } catch { return null; }
}

export const tokenStorage = {
  getAccess: (): string | null => ls(() => localStorage.getItem(ACCESS_KEY)),
  getRefresh: (): string | null => ls(() => localStorage.getItem(REFRESH_KEY)),
  set: (access: string, refresh: string): void => {
    try {
      localStorage.setItem(ACCESS_KEY, access);
      localStorage.setItem(REFRESH_KEY, refresh);
    } catch { /* ignore */ }
  },
  clear: (): void => {
    try {
      localStorage.removeItem(ACCESS_KEY);
      localStorage.removeItem(REFRESH_KEY);
    } catch { /* ignore */ }
  },
};
