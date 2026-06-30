/** Design tokens — single source of truth for colors, type, and spacing. */

export const colors = {
  primary: "#4F46E5",      // indigo-600
  primaryHover: "#4338CA", // indigo-700
  secondary: "#6B7280",    // gray-500
  success: "#10B981",      // emerald-500
  danger: "#EF4444",       // red-500
  warning: "#F59E0B",      // amber-500
  surface: "#FFFFFF",
  surfaceMuted: "#F9FAFB", // gray-50
  border: "#E5E7EB",       // gray-200
  text: "#111827",         // gray-900
  textMuted: "#6B7280",    // gray-500
  textInverse: "#FFFFFF",
  voteActive: "#4F46E5",   // indigo — cast vote state
  voteInactive: "#9CA3AF", // gray-400
} as const;

export const fontSize = {
  xs: 12,
  sm: 14,
  base: 16,
  lg: 18,
  xl: 20,
  "2xl": 24,
  "3xl": 30,
} as const;

export const fontWeight = {
  normal: "400",
  medium: "500",
  semibold: "600",
  bold: "700",
} as const;

export const spacing = {
  1: 4,
  2: 8,
  3: 12,
  4: 16,
  5: 20,
  6: 24,
  8: 32,
  10: 40,
  12: 48,
} as const;

export const borderRadius = {
  sm: 4,
  md: 8,
  lg: 12,
  xl: 16,
  full: 9999,
} as const;

export const shadow = {
  sm: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 1 },
    shadowOpacity: 0.05,
    shadowRadius: 2,
    elevation: 1,
  },
  md: {
    shadowColor: "#000",
    shadowOffset: { width: 0, height: 2 },
    shadowOpacity: 0.1,
    shadowRadius: 4,
    elevation: 3,
  },
} as const;

export type ColorKey = keyof typeof colors;
export type SpacingKey = keyof typeof spacing;
