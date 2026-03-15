# Profiles API Documentation
Base URL: /api/profiles/
Authentication: All endpoints use JWT Bearer Token unless marked as Public.

---
### GET /api/profiles/student/
**Description:** Retrieve the authenticated student's profile.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Student only

**Request Headers:**
Authorization: Bearer <your_jwt_token>

**Request Body:**
None

**Example Request:**
```http
GET /api/profiles/student/
Authorization: Bearer <token>
```

**Example Response (Success):**
```json
{
  "id": "uuid",
  "university": "Cairo University",
  "major": "Computer Science",
  "graduation_year": 2024,
  "gpa": 3.8,
  "bio": "Passionate developer...",
  "phone": "0123456789",
  "is_profile_public": true,
  "hide_gpa": false,
  "hide_phone": false,
  "skills": [
    { "id": 1, "name": "Python", "category": "technical" }
  ]
}
```

**Response Status Codes:**
200 OK | 401 Unauthorized | 404 Not found

---
### PATCH /api/profiles/student/
**Description:** Update the authenticated student's profile.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Student only (Owner)

**Request Headers:**
Authorization: Bearer <your_jwt_token>
Content-Type: multipart/form-data

**Request Body (multipart/form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| university | string | No | University name |
| major | string | No | Engineering, CS, etc. |
| graduation_year | integer | No | Year of graduation |
| gpa | decimal | No | GPA value |
| bio | text | No | Short biography |
| phone | string | No | Contact number |
| is_profile_public | boolean | No | Publicly visible or not |
| hide_gpa | boolean | No | Mask GPA in public view |
| hide_phone | boolean | No | Mask phone in public view |
| skill_ids | array (int) | No | List of skill IDs |

**Example Request:**
```http
PATCH /api/profiles/student/
Authorization: Bearer <token>
Content-Type: application/json

{
  "bio": "Updated bio...",
  "skill_ids": [1, 2, 5]
}
```

**Example Response (Success):**
```json
{ "..." }
```

**Response Status Codes:**
200 OK | 400 Validation error | 401 Unauthorized

---
### GET /api/profiles/student/<uuid:user_id>/
**Description:** Retrieve a student's profile by their user ID.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| user_id | uuid | Yes | The ID of the user whose profile to retrieve |

**Request Headers:**
Authorization: Bearer <your_jwt_token>

**Example Request:**
```http
GET /api/profiles/student/550e8400-e29b-41d4-a716-446655440000/
Authorization: Bearer <token>
```

**Example Response (Success):**
```json
{ "..." }
```
⚠️ Note: Response fields are filtered based on the profile's privacy settings (`is_profile_public`, `hide_gpa`, `hide_phone`) if the requester is not the owner or staff.

**Response Status Codes:**
200 OK | 401 Unauthorized | 404 Not found

---
### GET /api/profiles/employer/
**Description:** Retrieve the authenticated employer's profile.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Employer only

**Request Headers:**
Authorization: Bearer <your_jwt_token>

**Example Request:**
```http
GET /api/profiles/employer/
Authorization: Bearer <token>
```

**Example Response (Success):**
```json
{
  "id": "uuid",
  "company_name": "Tech Corp",
  "industry": "Software",
  "company_size": "51-200",
  "website": "https://techcorp.io",
  "logo_url": "https://...",
  "phone": "0987654321",
  "is_profile_public": true,
  "hide_phone": false
}
```

**Response Status Codes:**
200 OK | 401 Unauthorized | 404 Not found

---
### PATCH /api/profiles/privacy/
**Description:** Endpoint to update privacy flags for the authenticated user's profile.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated

**Request Headers:**
Authorization: Bearer <your_jwt_token>
Content-Type: application/json

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| is_profile_public | boolean | No | Toggle public visibility |
| hide_phone | boolean | No | Toggle phone visibility |
| hide_gpa | boolean | No | Toggle GPA visibility (Student only) |

**Example Request:**
```http
PATCH /api/profiles/privacy/
Authorization: Bearer <token>
Content-Type: application/json

{
  "is_profile_public": false
}
```

**Example Response (Success):**
```json
{ "..." }
```

**Response Status Codes:**
200 OK | 400 Validation error | 401 Unauthorized
