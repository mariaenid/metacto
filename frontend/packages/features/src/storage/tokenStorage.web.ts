const KEY = "metacto_access_token";

export const tokenStorage = {
  get: (): string | null => {
    try { return localStorage.getItem(KEY); } catch { return null; }
  },
  set: (token: string): void => {
    try { localStorage.setItem(KEY, token); } catch { /* ignore */ }
  },
  clear: (): void => {
    try { localStorage.removeItem(KEY); } catch { /* ignore */ }
  },
};
