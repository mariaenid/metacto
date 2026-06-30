# 04 — Authentication

## Context
The system requires authenticated identity for all write actions (submit, upvote, status transitions, comments). Reads remain public. Auth must work consistently across the Next.js web app and the Expo mobile app, stay collision-safe under high concurrency (see [[03-concurrency-and-collision-safety]]), and demonstrate production-grade security — not the shortcut version.

## Decision

### Method
Email + password. Universal, no third-party dependency, full control over the credential flow.

### Tokens
- **Access token:** JWT (HS256), 15 minute lifetime, carries `user_id`, `role`, `email_verified`. Held in memory on both clients; never written to localStorage or AsyncStorage.
- **Refresh token:** opaque random string (32 bytes, base64url), 30 day lifetime, **rotating**. Each successful refresh issues a new refresh token and invalidates the previous one.
- **Breach detection:** if a refresh token is presented that has already been used (`used_at IS NOT NULL`), the entire token family for that user is invalidated and the user must log in again. This catches stolen tokens.

### Storage
- **Mobile (Expo):** refresh token in `expo-secure-store` (iOS Keychain / Android Keystore, hardware-backed where available).
- **Web (Next.js):** refresh token in an `httpOnly`, `Secure`, `SameSite=Strict` cookie scoped to the auth endpoint path. Access token in memory only.

### Email verification
- `User.email_verified` (boolean, default `false`).
- Verification email is sent on registration with a single-use `EmailVerificationToken` (24h TTL).
- Write endpoints (submit, vote, comment) require `email_verified = true`. Login does not.
- The verification token is consumed atomically via `UPDATE ... WHERE used_at IS NULL`; concurrent verifications from a double-click result in one success and one `410 Gone`.

### Password
- Hashed with Argon2id, parameters: `m = 64MB, t = 3, p = 4`. Configurable via environment.
- Reset flow: user requests reset → server issues `PasswordResetToken` (single-use, 1h TTL) → email link → form submits new password → token consumed atomically.

### Rate limiting (Redis atomic `INCR` + `EXPIRE`)
- Login: 5 attempts per IP per 10 minutes; after that returns `429` for the window.
- Register: 3 per IP per hour.
- Password reset request: 3 per email per day.
- Email verification resend: 3 per user per day.

### Concurrency safety on auth
- **Login race:** look up user by email, verify password hash (CPU-bound, no DB contention), update `last_login_at` via a non-blocking UPDATE. No collision concerns.
- **Refresh rotation:**
  ```sql
  BEGIN;
  SELECT * FROM refresh_tokens WHERE token = $1 FOR UPDATE;
  -- if used_at IS NOT NULL → mark family invalid + COMMIT + return 401
  UPDATE refresh_tokens SET used_at = NOW() WHERE token = $1 AND used_at IS NULL;
  INSERT INTO refresh_tokens (user_id, family_id, token, expires_at) VALUES ($u, $f, $t, $exp);
  COMMIT;
  ```
- **Registration race:** unique constraint on `email`; concurrent registrations return one success and one `409 Conflict`.
- **Logout / "log out all sessions":** `UPDATE refresh_tokens SET used_at = NOW() WHERE user_id = $1 AND used_at IS NULL` — atomic and idempotent.

## Consequences
- Three new entities: `RefreshToken`, `EmailVerificationToken`, `PasswordResetToken`. Each has its own table with a unique index on the token value and a partial index on `used_at IS NULL`.
- Auth endpoints add seven routes: register, verify-email, login, refresh, logout, request-password-reset, confirm-password-reset. Each is rate-limited in Redis and tested independently.
- The mobile client needs SecureStore wiring; the web client needs cookie-based refresh on the API client.
- Argon2id parameters are tunable per deployment; the trade-off is documented (security vs login latency).
- The `email_verified` gate is enforced in the API permission layer, not in the UI. UI may also hide actions but never as the sole barrier.
