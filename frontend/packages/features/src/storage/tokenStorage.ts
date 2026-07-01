// Base type declaration for tsc. Platform bundlers (webpack/Metro) resolve to .web.ts or .native.ts.
export declare const tokenStorage: {
  getAccess: () => string | null;
  getRefresh: () => string | null;
  set: (access: string, refresh: string) => void;
  clear: () => void;
};
