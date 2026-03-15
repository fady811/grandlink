# GrandLink API Documentation

Comprehensive API reference for the GrandLink backend.

---

## 🔐 Authentication

### **Register User**

* **Path:** `/api/auth/register/`
* **Method:** `POST`
* **Auth Required:** `No`
* **Description:** Creates a new user account (inactive) and triggers a 6-digit OTP email.

**Request Body:**

```json
{
  "email": "string (Email)",
  "password": "string",
  "password2": "string (Matches password)",
  "role": "string (student|employer)"
}
```

**Success Response (201 Created):**

```json
{
  "message": "User created. Please verify your email with OTP.",
  "email": "user@example.com"
}
```

---

### **Verify OTP**

* **Path:** `/api/auth/verify-otp/`
* **Method:** `POST`
* **Auth Required:** `No`
* **Description:** Verifies the user email via code and returns JWT access/refresh tokens.

**Request Body:**

```json
{
  "email": "string",
  "code": "string (6 chars)"
}
```

**Success Response (200 OK):**

```json
{
  "message": "Email verified successfully.",
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token"
}
```

---

### **Login**

* **Path:** `/api/auth/login/`
* **Method:** `POST`
* **Auth Required:** `No`
* **Description:** Authenticates user and returns JWT tokens along with user details.

**Request Body:**

```json
{
  "email": "string",
  "password": "string"
}
```

**Success Response (200 OK):**

```json
{
  "access": "jwt_access_token",
  "refresh": "jwt_refresh_token",
  "user": {
    "id": "uuid",
    "email": "string",
    "role": "string",
    "is_active": "boolean",
    "date_joined": "iso-date"
  }
}
```

---

### **Google Authentication**

* **Path:** `/api/auth/google/`
* **Method:** `POST`
* **Auth Required:** `No`
* **Description:** Validates Google ID token. Auto-creates/activates user.

**Request Body:**

```json
{
  "token": "string (Google ID Token)",
  "role": "string"
}
```

---

## 👤 Profiles

### **Retrieve/Update Student Profile**

* **Path:** `/api/profiles/student/` or `/api/profiles/student/<user_id>/`
* **Method:** `GET`, `PUT`, `PATCH`
* **Auth Required:** `Yes (Owner or Admin)`
* **Description:** Manage detailed student profile information.

**Request/Response Fields:**

* `university`: string
* `major`: string
* `graduation_year`: integer
* `gpa`: decimal (string in JSON)
* `skills`: array [string]
* `bio`: string
* `phone`: string
* `hide_gpa`: boolean
* `hide_phone`: boolean
* `is_profile_public`: boolean

**Example Request:**

```json
{
  "university": "State University",
  "major": "Data Science",
  "graduation_year": 2024,
  "skills": ["SQL", "Tableau"]
}
```

---

### **Retrieve/Update Employer Profile**

* **Path:** `/api/profiles/employer/` or `/api/profiles/employer/<user_id>/`
* **Method:** `GET`, `PUT`, `PATCH`
* **Auth Required:** `Yes (Owner or Admin)`
* **Description:** Manage employer/company details.

**Request/Response Fields:**

* `company_name`: string (Required)
* `industry`: string
* `company_size`: string (e.g., "11-50")
* `website`: url-string
* `phone`: string
* `is_verified`: boolean (Read-only for users)
* `hide_phone`: boolean
* `is_profile_public`: boolean

---

### **Global Privacy Settings**

* **Path:** `/api/profiles/privacy/`
* **Method:** `PATCH`
* **Auth Required:** `Yes`
* **Description:** Partial update for privacy flags on the authenticated user's profile.

**Request Body:**

```json
{
  "is_profile_public": false,
  "hide_gpa": true
}
```

---

## 📝 Status Codes

| Code | Description |
|---|---|
| 200 | OK (Success) |
| 201 | Created (Success) |
| 400 | Bad Request (Validation Error) |
| 401 | Unauthorized (Missing/Invalid Token) |
| 403 | Forbidden (Permission Denied) |
| 404 | Not Found |
| 500 | Internal Server Error |
