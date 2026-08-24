# Security

## Authentication & sessions
- Argon2id password hashing; timing-equalized verification for unknown users.
- JWT with strict algorithm allow-list; separate access/refresh secrets.
- Refresh-token rotation with family tracking + reuse detection (family revocation).
- HttpOnly, Secure (in prod), SameSite=strict refresh cookie scoped to /api/v1/auth.
- Account lockout after repeated failures.

## Client portal
- Case Number alone never grants access; OTP + scoped session required.
- OTP: crypto-secure, hashed at rest (HMAC bound to ticket), TTL, attempt cap,
  resend cooldown, Redis abuse guard. Raw OTP never logged or returned in prod.
- Anti-enumeration: identical responses for case/email match or miss.
- Client session scoped to a single ticket; cannot reach admin APIs (RBAC + kind).

## Input & transport
- Rate limiting (Redis, atomic) on ticket creation + OTP requests.
- Trusted-proxy client IP resolution; arbitrary X-Forwarded-For is not trusted.
- Turnstile CAPTCHA verified server-side, fails closed.
- Body-size limit + security headers (CSP, X-Content-Type-Options, HSTS in prod).
- Consistent error envelope; stack traces never returned to clients.

## Uploads
- Filename/extension/MIME/magic-byte/size/null-byte/traversal validation.
- ClamAV scan; unknown scan status fails closed. Opaque storage keys, no paths exposed.

## Secrets
- All secrets via environment. Production refuses weak/placeholder/short secrets
  and identical access/refresh secrets. Nothing sensitive is committed.

## Verification status
Security controls are IMPLEMENTED. Automated security tooling (Bandit, pip-audit,
detect-secrets) is configured in CI but was NOT executed in the build sandbox
(no dependencies/internet). No "zero vulnerabilities" claim is made.
