# Authentication API Documentation
Base URL: /api/auth/
Authentication: All endpoints use JWT Bearer Token unless marked as Public.

---
### POST /api/auth/register/
**Description:** User registration (creates inactive user and sends OTP).
**Authentication:** Public
**Permissions:** AllowAny

**Request Headers:**
Content-Type: application/json

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | Valid email address |
| password | string | Yes | At least 8 characters, checked against common passwords |
| password2 | string | Yes | Must match password |
| role | string | Yes | One of: student | employer |

**Example Request:**
```http
POST /api/auth/register/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "hashed_password_123",
  "password2": "hashed_password_123",
  "role": "student"
}
```

**Example Response (Success):**
```json
{
  "message": "User created. Please verify your email with OTP.",
  "email": "user@example.com"
}
```

**Response Status Codes:**
201 Created | 400 Validation error

---
### POST /api/auth/verify-otp/
**Description:** Verifies user email using the code sent during registration and returns tokens.
**Authentication:** Public
**Permissions:** AllowAny

**Request Headers:**
Content-Type: application/json

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's email |
| code | string | Yes | 6-digit OTP code |

**Example Request:**
```http
POST /api/auth/verify-otp/
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456"
}
```

**Example Response (Success):**
```json
{
  "message": "Email verified successfully.",
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token"
}
```

**Response Status Codes:**
200 OK | 400 Validation error

---
### POST /api/auth/resend-otp/
**Description:** Resends a new OTP to the user's email if the account is not yet active.
**Authentication:** Public
**Permissions:** AllowAny

**Request Headers:**
Content-Type: application/json

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's email |

**Example Request:**
```http
POST /api/auth/resend-otp/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Example Response (Success):**
```json
{
  "message": "New OTP sent."
}
```

**Response Status Codes:**
200 OK | 400 Validation error | 404 Not found

---
### POST /api/auth/login/
**Description:** Authenticates user and returns JWT tokens.
**Authentication:** Public
**Permissions:** AllowAny

**Request Headers:**
Content-Type: application/json

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's email |
| password | string | Yes | User's password |

**Example Request:**
```http
POST /api/auth/login/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Example Response (Success):**
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": "uuid",
    "email": "user@example.com",
    "role": "student",
    "is_active": true,
    "date_joined": "iso-date",
    "last_login": "iso-date"
  }
}
```

**Response Status Codes:**
200 OK | 401 Unauthorized | 403 Forbidden

---
### POST /api/auth/token/refresh/
**Description:** Refreshes an expired access token using a refresh token.
**Authentication:** Public
**Permissions:** AllowAny

**Request Headers:**
Content-Type: application/json

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| refresh | string | Yes | Valid refresh token |

**Example Request:**
```http
POST /api/auth/token/refresh/
Content-Type: application/json

{
  "refresh": "jwt_refresh_token"
}
```

**Example Response (Success):**
```json
{
  "access": "new_jwt_access_token"
}
```

**Response Status Codes:**
200 OK | 401 Unauthorized

---
### POST /api/auth/logout/
**Description:** Blacklists the refresh token and logs out the user.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated

**Request Headers:**
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| refresh | string | Yes | Refresh token to blacklist |

**Example Request:**
```http
POST /api/auth/logout/
Authorization: Bearer <token>
Content-Type: application/json

{
  "refresh": "jwt_refresh_token"
}
```

**Example Response (Success):**
```json
{}
```

**Response Status Codes:**
200 OK | 401 Unauthorized

---
### POST /api/auth/google/
**Description:** Authenticates or registers a user via Google ID Token.
**Authentication:** Public
**Permissions:** AllowAny

**Request Headers:**
Content-Type: application/json

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| token | string | Yes | Google ID Token |
| role | string | Yes | One of: student | employer |

**Example Request:**
```http
POST /api/auth/google/
Content-Type: application/json

{
  "token": "google_id_token",
  "role": "student"
}
```

**Example Response (Success):**
```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": { "..." }
}
```

**Response Status Codes:**
200 OK | 400 Validation error

---
### POST /api/auth/password-reset/
**Description:** Sends a password-reset OTP to the user's email.
**Authentication:** Public
**Permissions:** AllowAny

**Request Headers:**
Content-Type: application/json

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's email |

**Example Request:**
```http
POST /api/auth/password-reset/
Content-Type: application/json

{
  "email": "user@example.com"
}
```

**Example Response (Success):**
```json
{
  "message": "If this email is registered, a reset code has been sent."
}
```

**Response Status Codes:**
200 OK

---
### POST /api/auth/password-reset/confirm/
**Description:** Verifies OTP and sets a new password.
**Authentication:** Public
**Permissions:** AllowAny

**Request Headers:**
Content-Type: application/json

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's email |
| code | string | Yes | 6-digit OTP code |
| new_password | string | Yes | New password |
| new_password2 | string | Yes | Confirm new password |

**Example Request:**
```http
POST /api/auth/password-reset/confirm/
Content-Type: application/json

{
  "email": "user@example.com",
  "code": "123456",
  "new_password": "new_secure_password",
  "new_password2": "new_secure_password"
}
```

**Example Response (Success):**
```json
{
  "message": "Password reset successfully. Please log in with your new password."
}
```

**Response Status Codes:**
200 OK | 400 Validation error | 404 Not found

---
### DELETE /api/auth/account/
**Description:** Soft-deletes the authenticated user's account.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated

**Request Headers:**
Authorization: Bearer <your_jwt_token>

**Request Body:**
None

**Example Request:**
```http
DELETE /api/auth/account/
Authorization: Bearer <token>
```

**Example Response (Success):**
```json
{
  "message": "Account scheduled for deletion. You may reactivate within 30 days."
}
```

**Response Status Codes:**
200 OK | 400 Validation error | 401 Unauthorized

---
### POST /api/auth/account/reactivate/
**Description:** Reactivates a soft-deleted account within 30 days.
**Authentication:** Public
**Permissions:** AllowAny

**Request Headers:**
Content-Type: application/json

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| email | string | Yes | User's email |
| password | string | Yes | User's password |

**Example Request:**
```http
POST /api/auth/account/reactivate/
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "password123"
}
```

**Example Response (Success):**
```json
{
  "message": "Account reactivated successfully.",
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token"
}
```

**Response Status Codes:**
200 OK | 400 Validation error | 401 Unauthorized
