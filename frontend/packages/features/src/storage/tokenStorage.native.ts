import * as SecureStore from "expo-secure-store";

const ACCESS_KEY = "metacto_access_token";
const REFRESH_KEY = "metacto_refresh_token";

export const tokenStorage = {
  getAccess: (): string | null => {
    try { return SecureStore.getItem(ACCESS_KEY); } catch { return null; }
  },
  getRefresh: (): string | null => {
    try { return SecureStore.getItem(REFRESH_KEY); } catch { return null; }
  },
  set: (access: string, refresh: string): void => {
    try {
      SecureStore.setItem(ACCESS_KEY, access);
      SecureStore.setItem(REFRESH_KEY, refresh);
    } catch { /* ignore */ }
  },
  clear: (): void => {
    try {
      SecureStore.deleteItemAsync(ACCESS_KEY);
      SecureStore.deleteItemAsync(REFRESH_KEY);
    } catch { /* ignore */ }
  },
};
