/**
 * Unit tests for auth business logic (pure functions, no network).
 */
import { describe, expect, it } from "vitest";

// --- password validation (matches backend RULE-11 / ADR-04) ---

function validatePassword(pw: string): string | null {
  if (pw.length < 8) return "Password must be at least 8 characters.";
  if (!/[A-Z]/.test(pw)) return "Password must contain an uppercase letter.";
  if (!/[0-9]/.test(pw)) return "Password must contain a digit.";
  return null;
}

describe("password validation", () => {
  it("accepts a strong password", () => {
    expect(validatePassword("CorrectHorseBattery1")).toBeNull();
  });

  it("rejects short passwords", () => {
    expect(validatePassword("Ab1")).toBe("Password must be at least 8 characters.");
  });

  it("rejects passwords without uppercase", () => {
    expect(validatePassword("allowercase1")).toBe(
      "Password must contain an uppercase letter.",
    );
  });

  it("rejects passwords without a digit", () => {
    expect(validatePassword("NoDigitsHere")).toBe(
      "Password must contain a digit.",
    );
  });
});

// --- email validation ---

function isValidEmail(email: string): boolean {
  return /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(email);
}

describe("email validation", () => {
  it("accepts a valid email", () => {
    expect(isValidEmail("user@example.com")).toBe(true);
  });

  it("rejects an email with no @", () => {
    expect(isValidEmail("notanemail")).toBe(false);
  });

  it("rejects an email with no domain", () => {
    expect(isValidEmail("user@")).toBe(false);
  });

  it("rejects an empty string", () => {
    expect(isValidEmail("")).toBe(false);
  });
});

// --- display name validation ---

describe("display name validation", () => {
  const validate = (name: string) => name.trim().length >= 1;

  it("accepts a non-empty name", () => {
    expect(validate("Alice")).toBe(true);
  });

  it("rejects an empty display name", () => {
    expect(validate("")).toBe(false);
  });

  it("rejects whitespace-only input", () => {
    expect(validate("   ")).toBe(false);
  });
});
