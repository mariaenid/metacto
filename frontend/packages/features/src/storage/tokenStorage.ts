// Base type declaration for tsc. Platform bundlers (webpack/Metro) resolve to .web.ts or .native.ts.
export declare const tokenStorage: {
  get: () => string | null;
  set: (token: string) => void;
  clear: () => void;
};
