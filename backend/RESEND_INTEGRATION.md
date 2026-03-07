# Resend Email Integration

This document covers the integration of [Resend](https://resend.com) as the transactional email provider for VibeCheck, replacing the previous simulated (console-only) email behavior.

---

## Overview

| Detail         | Value                          |
| -------------- | ------------------------------ |
| Provider       | Resend                         |
| Sending domain | `vibeaura.app`                 |
| From address   | `noreply@vibeaura.app`         |
| Package        | `resend==2.0.0`                |

Two email types are now sent for real:

1. **Email verification** -- sent when a new user registers.
2. **Password reset** -- sent when a user requests a password reset.

---

## What changed

### 1. New dependency

**File:** `backend/requirements.txt`

Added the Resend Python SDK:

```
resend==2.0.0
```

### 2. New environment variables

**File:** `backend/.env` (and `.env.example`)

Three new variables were added under the `# Email (Resend)` section:

```env
RESEND_API_KEY=re_xxxxx          # Your Resend API key
EMAIL_FROM_ADDRESS=noreply@vibeaura.app   # Sender address (must match verified domain)
FRONTEND_URL=http://localhost:5173        # Base URL for links inside emails
```

### 3. Configuration loading

**File:** `backend/app/config.py`

The `Config` class now reads the three new env vars so they are available via `current_app.config`:

```python
# Email (Resend)
RESEND_API_KEY = os.getenv('RESEND_API_KEY')
EMAIL_FROM_ADDRESS = os.getenv('EMAIL_FROM_ADDRESS', 'noreply@vibeaura.app')
FRONTEND_URL = os.getenv('FRONTEND_URL', 'http://localhost:5173')
```

### 4. Email service module (new file)

**File:** `backend/app/services/email_service.py`

A dedicated service module with two public functions:

| Function                      | Purpose                                          |
| ----------------------------- | ------------------------------------------------ |
| `send_verification_email()`   | Sends a verification link to a newly registered user |
| `send_password_reset_email()` | Sends a password reset link to an existing user   |

Both functions:

- Read `RESEND_API_KEY`, `EMAIL_FROM_ADDRESS`, and `FRONTEND_URL` from Flask config.
- Build an HTML email using inline-styled templates.
- Call `resend.Emails.send()` to dispatch the email.
- Log the Resend email ID on success.

Internal helpers:

| Helper                    | Purpose                              |
| ------------------------- | ------------------------------------ |
| `_get_resend_client()`    | Sets the API key on the Resend SDK   |
| `_verification_html()`    | Returns the verification email HTML  |
| `_reset_password_html()`  | Returns the password reset email HTML |

### 5. Auth routes updated

**File:** `backend/app/routes/auth.py`

**Registration (`POST /api/v1/auth/register`)**

Before (simulated):
```python
if current_app.debug:
    print(f"EMAIL VERIFICATION for {email}")
    print(f"Token: {raw_token}")
```

After (real):
```python
try:
    send_verification_email(email, username, raw_token)
except Exception as mail_err:
    current_app.logger.error(f"Failed to send verification email to {email}: {mail_err}")
```

**Forgot password (`POST /api/v1/auth/forgot-password`)**

Before (simulated):
```python
if current_app.debug:
    print(f"PASSWORD RESET for {email}")
    print(f"Token: {raw_token}")
```

After (real):
```python
try:
    send_password_reset_email(email, user.username, raw_token)
except Exception as mail_err:
    current_app.logger.error(f"Failed to send password reset email to {email}: {mail_err}")
```

Both are wrapped in try/except so a Resend API failure does not break the HTTP response.

---

## Email templates

Both templates use a dark-themed, inline-styled HTML layout that matches the app aesthetic:

- **Background:** `#0f0f0f` (dark)
- **Card:** `#1a1a2e` (dark navy) with `16px` border radius
- **Header gradient:** `#667eea` to `#764ba2` (purple-blue)
- **CTA button:** Same gradient as header
- **Typography:** System font stack (`-apple-system, BlinkMacSystemFont, Segoe UI, Roboto`)

### Verification email

- **Subject:** "Verify your VibeCheck account"
- **CTA:** "Verify My Email" button linking to `{FRONTEND_URL}/verify-email?token={token}`
- **Expiry note:** 24 hours

### Password reset email

- **Subject:** "Reset your VibeCheck password"
- **CTA:** "Reset Password" button linking to `{FRONTEND_URL}/reset-password?token={token}`
- **Expiry note:** 1 hour

---

## File summary

```
backend/
  requirements.txt              # + resend==2.0.0
  .env                          # + RESEND_API_KEY, EMAIL_FROM_ADDRESS, FRONTEND_URL
  .env.example                  # + same three variables (placeholder values)
  app/
    config.py                   # + RESEND_API_KEY, EMAIL_FROM_ADDRESS, FRONTEND_URL
    services/
      email_service.py          # NEW -- Resend integration and HTML templates
    routes/
      auth.py                   # MODIFIED -- register and forgot-password now send real emails
  tests/
    unit/
      test_email_service.py     # NEW -- 42 unit tests (mocked Resend, Flask test client)
    integration/
      test_email_integration.py # NEW -- 15 integration tests (live backend, real Resend)
```

---

## Tests

### Test strategy

| Layer | File | Tests | Runner | Dependencies |
| ----- | ---- | ----: | ------ | ------------ |
| Unit | `tests/unit/test_email_service.py` | 42 | Flask test client + SQLite | None (Resend is mocked) |
| Integration | `tests/integration/test_email_integration.py` | 15 | `requests` against live backend | Docker (`docker compose up`) |

- **Unit tests** mock `resend.Emails.send` so they run fast, offline, and never send real emails.
- **Integration tests** hit the running backend and exercise the real Resend API path, validating that endpoints return correct responses without errors.

### Unit tests (42 tests)

**File:** `tests/unit/test_email_service.py`

#### TestSendVerificationEmail (7 tests)

Tests `send_verification_email()` in isolation with a mocked Resend SDK.

| Test | What it verifies |
| ---- | ---------------- |
| `test_calls_resend_api` | `resend.Emails.send` is called exactly once |
| `test_sends_to_correct_recipient` | `to` field contains the target email |
| `test_from_address_matches_config` | `from` field uses `EMAIL_FROM_ADDRESS` and includes "VibeCheck" |
| `test_subject_is_verification` | Subject line contains "verify" or "verification" |
| `test_html_contains_verification_url` | Email body includes `{FRONTEND_URL}/verify-email?token={token}` |
| `test_html_contains_username` | Email body greets the user by username |
| `test_returns_resend_response` | Returns the dict from the Resend API (contains email ID) |

#### TestSendPasswordResetEmail (6 tests)

Same coverage as above, applied to `send_password_reset_email()`.

| Test | What it verifies |
| ---- | ---------------- |
| `test_calls_resend_api` | `resend.Emails.send` is called exactly once |
| `test_sends_to_correct_recipient` | `to` field contains the target email |
| `test_subject_is_password_reset` | Subject line contains "reset" |
| `test_html_contains_reset_url` | Email body includes `{FRONTEND_URL}/reset-password?token={token}` |
| `test_html_contains_username` | Email body addresses the user by username |
| `test_from_address_matches_config` | `from` field uses `EMAIL_FROM_ADDRESS` |

#### TestGetResendClient (2 tests)

| Test | What it verifies |
| ---- | ---------------- |
| `test_raises_without_api_key` | `RuntimeError` raised when `RESEND_API_KEY` is `None` |
| `test_raises_with_empty_string_key` | `RuntimeError` raised when `RESEND_API_KEY` is `""` |

#### TestEmailHtmlTemplates (8 tests)

Tests the HTML template helper functions directly (no mocking needed).

| Test | What it verifies |
| ---- | ---------------- |
| `test_verification_html_has_cta_button` | "Verify My Email" text and correct `href` present |
| `test_verification_html_has_expiry_notice` | "24 hours" expiry note present |
| `test_reset_html_has_cta_button` | "Reset Password" text and correct `href` present |
| `test_reset_html_has_expiry_notice` | "1 hour" expiry note present |
| `test_verification_html_is_valid_html` | Contains `<!DOCTYPE html>`, `</body>`, `</html>` |
| `test_reset_html_is_valid_html` | Same structural validation for reset template |
| `test_verification_html_escapes_special_chars_in_url` | URL with `&` is preserved in HTML |
| `test_reset_html_escapes_special_chars_in_url` | Same for reset template |

#### TestRegistrationSendsEmail (7 tests)

Tests that `POST /auth/register` correctly calls the email service (mocked at the route level).

| Test | What it verifies |
| ---- | ---------------- |
| `test_register_calls_send_verification_email` | `send_verification_email` is called once |
| `test_register_passes_correct_email` | First arg matches the registrant's email |
| `test_register_passes_correct_username` | Second arg matches the registrant's username |
| `test_register_passes_a_token` | Third arg is a non-empty token string (>10 chars) |
| `test_register_succeeds_when_email_fails` | Returns 201 even if Resend throws an exception |
| `test_register_user_created_despite_email_failure` | User exists in DB after email failure |
| `test_register_response_shape_unchanged` | Response body has `message`, `user`, `emailVerificationRequired`; no `token` |

#### TestForgotPasswordSendsEmail (8 tests)

Tests that `POST /auth/forgot-password` correctly calls the email service.

| Test | What it verifies |
| ---- | ---------------- |
| `test_forgot_password_calls_send_email` | `send_password_reset_email` is called for verified users |
| `test_forgot_password_passes_correct_email` | First arg matches the request email |
| `test_forgot_password_passes_username` | Second arg matches the user's username |
| `test_forgot_password_passes_token` | Third arg is a non-empty token string |
| `test_forgot_password_succeeds_when_email_fails` | Returns 200 even if Resend throws |
| `test_no_email_for_nonexistent_user` | `send_password_reset_email` is never called |
| `test_no_email_for_unverified_user` | `send_password_reset_email` is never called |
| `test_forgot_password_response_is_generic` | Same message for existing and non-existing users (security) |

#### TestEmailConfig (4 tests)

| Test | What it verifies |
| ---- | ---------------- |
| `test_resend_api_key_in_config` | `RESEND_API_KEY` is not `None` |
| `test_email_from_address_in_config` | Equals `noreply@vibeaura.app` |
| `test_frontend_url_in_config` | Equals `http://localhost:5173` |
| `test_frontend_url_has_no_trailing_slash` | No trailing `/` in the URL |

### Integration tests (15 tests)

**File:** `tests/integration/test_email_integration.py`

All tests are marked `@pytest.mark.integration` and require `docker compose up`.

#### TestRegistrationEmail (7 tests)

| Test | What it verifies |
| ---- | ---------------- |
| `test_register_returns_201` | Registration succeeds with real Resend wired in |
| `test_register_response_has_email_required_flag` | `emailVerificationRequired` is `true` |
| `test_register_does_not_issue_jwt` | No `token` in response body |
| `test_register_user_is_unverified` | `user.emailVerified` is `false` |
| `test_register_message_mentions_email` | Response message contains "email" |
| `test_duplicate_email_still_returns_409` | Duplicate detection still works |
| `test_invalid_email_still_returns_400` | Validation runs before email attempt |

#### TestForgotPasswordEmail (6 tests)

| Test | What it verifies |
| ---- | ---------------- |
| `test_forgot_password_returns_200` | Returns 200 for verified user (real email sent) |
| `test_forgot_password_generic_message` | Same message for existing and fake emails |
| `test_forgot_password_nonexistent_email_no_error` | No 500 for unknown emails |
| `test_forgot_password_unverified_user_no_error` | No 500 for unverified users |
| `test_forgot_password_missing_email_returns_400` | Validation catches missing field |
| `test_forgot_password_invalid_email_returns_400` | Validation catches bad format |

#### TestFullEmailFlow (2 tests)

| Test | What it verifies |
| ---- | ---------------- |
| `test_register_verify_login_reset_login` | Complete lifecycle: register, verify (DB), login, forgot-password, reset-password, login with new password, old password rejected |
| `test_login_blocked_until_verified` | Login returns 403 before verification, 200 after |

### Pytest discovery

Both test files live inside the existing `backend/tests/` tree and follow the project's `pytest.ini` conventions (`test_*.py` naming, `Test*` classes, `test_*` functions). Pytest auto-discovers all 57 tests:

```
tests/
  unit/
    test_email_service.py       # 42 tests -- discovered automatically
  integration/
    test_email_integration.py   # 15 tests -- marked @pytest.mark.integration
```

To confirm discovery:

```bash
python -m pytest --collect-only tests/unit/test_email_service.py tests/integration/test_email_integration.py
```

### Running the tests

**Unit tests** (no Docker needed):

```bash
cd backend
python -m pytest tests/unit/test_email_service.py -v
```

**Integration tests** (requires Docker backend):

```bash
docker compose up -d
python -m pytest tests/integration/test_email_integration.py -v
```

**All email tests together:**

```bash
python -m pytest tests/unit/test_email_service.py tests/integration/test_email_integration.py -v
```

**All project tests:**

```bash
# Unit only (fast, offline)
python -m pytest tests/unit/ -v

# Integration only (requires running backend)
python -m pytest tests/integration/ -v -m integration

# Everything
python -m pytest tests/ -v
```

### Test results

All 57 tests pass:

```
tests/unit/test_email_service.py         42 passed
tests/integration/test_email_integration.py  15 passed
============================= 57 passed in 18.23s ==============================
```

---

## How to run

```bash
cd backend
docker compose up --build -d
```

The backend container will install `resend` from `requirements.txt` during the Docker build and read the API key from `.env` at runtime.

---

## Verification

After starting the backend, you can confirm emails are being sent by checking the container logs:

```bash
docker logs vibecheck_backend --tail 20
```

A successful send looks like:

```
INFO in email_service: Verification email sent to user@example.com (id=abc123-...)
```

You can also verify delivery in the [Resend dashboard](https://resend.com/emails).

---

## Live audit

### End-to-end flow verification

Each step was executed against the running backend and confirmed:

| Step | Action | Expected | Result |
| ---- | ------ | -------- | ------ |
| 1 | `POST /auth/register` | 201, `emailVerificationRequired: true` | 201 |
| 2 | Check backend logs | Resend email ID logged | `id=1c5662c6-...` |
| 3 | `POST /auth/login` (before verify) | 403 Forbidden | 403 |
| 4 | Verify email via DB | `email_verified = true` | Updated |
| 5 | `POST /auth/login` (after verify) | 200 + JWT | 200 |
| 6 | `POST /auth/forgot-password` | 200, reset email sent | `id=ee82a875-...` |
| 7 | `POST /auth/reset-password` | 200 | 200 |
| 8 | Login with old password | 401 | 401 |
| 9 | Login with new password | 200 | 200 |

### Edge cases

| Scenario | Expected | Result |
| -------- | -------- | ------ |
| Forgot password for non-existent email | 200 (no info leak) | 200 |
| Forgot password for unverified user | 200 (no email sent) | 200 |
| Register with invalid email format | 400 | 400 |
| Reset with invalid token | 400 | 400 |
| Reset with already-used token | 400 | 400 |
| Verify with bad token | 404 | 404 |
| Verify with missing token | 400 | 400 |

### Frontend-backend alignment

Every URL, route, and parameter was cross-checked between the email templates, the frontend components, and the backend endpoints.

| Component | Email URL / Frontend route | Backend endpoint | Aligned |
| --------- | -------------------------- | ---------------- | ------- |
| Verification | `{FRONTEND_URL}/verify-email?token={token}` | `GET /auth/verify-email?token=` | Yes |
| Password reset | `{FRONTEND_URL}/reset-password?token={token}` | `POST /auth/reset-password` `{token, newPassword}` | Yes |

| Frontend file | What it does | Backend match |
| ------------- | ------------ | ------------- |
| `Register.jsx` | Shows "check your email" after 201 | `emailVerificationRequired: true` |
| `VerifyEmail.jsx` | Reads `?token=`, calls `GET /auth/verify-email` | `request.args.get('token')` |
| `ForgotPassword.jsx` | Posts `{email}` to `/auth/forgot-password` | Expects `{email}` |
| `ResetPassword.jsx` | Reads `?token=`, posts `{token, newPassword}` to `/auth/reset-password` | Expects `{token, newPassword}` |
| `Login.jsx` | Shows verification message on 403 | Returns 403 when `!email_verified` |

| Config | Value | Consistent |
| ------ | ----- | ---------- |
| `FRONTEND_URL` in `.env` | `http://localhost:5173` | Matches Vite default port |
| `EMAIL_FROM_ADDRESS` | `noreply@vibeaura.app` | Matches verified Resend domain |
| Docker `env_file: .env` | Loads all email vars into container | Yes |
