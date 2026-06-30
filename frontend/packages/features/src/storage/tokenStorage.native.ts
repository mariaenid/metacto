import * as SecureStore from "expo-secure-store";

const KEY = "metacto_access_token";

export const tokenStorage = {
  get: (): string | null => {
    // SecureStore is sync on iOS/Android via the native bridge.
    try { return SecureStore.getItem(KEY); } catch { return null; }
  },
  set: (token: string): void => {
    try { SecureStore.setItem(KEY, token); } catch { /* ignore */ }
  },
  clear: (): void => {
    try { SecureStore.deleteItemAsync(KEY); } catch { /* ignore */ }
  },
};
