# GradLink API Documentation

| App | File | Endpoints | Public Endpoints |
|-----|------|-----------|-----------------|
| Authentication | [authentication.md](authentication.md) | 11 | Register, Login, OTP, OAuth, Password Reset, Reactivate |
| Profiles | [profiles.md](profiles.md) | 5 | None |
| Jobs | [jobs.md](jobs.md) | 16 | None |
| Interviews | [interviews.md](interviews.md) | 7 | None |
| Notifications | [notifications.md](notifications.md) | 4 | None |
| Support | [support.md](support.md) | 4 | None |
| Billing | [billing.md](billing.md) | 2 | Plans |

## Full List of Public Endpoints
- `POST /api/auth/register/`
- `POST /api/auth/verify-otp/`
- `POST /api/auth/resend-otp/`
- `POST /api/auth/login/`
- `POST /api/auth/token/refresh/`
- `POST /api/auth/google/`
- `POST /api/auth/password-reset/`
- `POST /api/auth/password-reset/confirm/`
- `POST /api/auth/account/reactivate/`
- `GET /api/billing/plans/`
