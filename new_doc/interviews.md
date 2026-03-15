# Interviews API Documentation
Base URL: /api/interviews/
Authentication: All endpoints use JWT Bearer Token unless marked as Public.

---
### GET /api/interviews/
**Description:** List interviews for the authenticated user (Employer sees own jobs', Student sees own).
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | string | No | scheduled | confirmed | completed | cancelled | no_show |
| job_id | uuid | No | Filter by job |
| application_id | uuid | No | Filter by application |

**Example Response (Success):**
```json
{
  "count": 5,
  "results": [
    {
      "id": "uuid",
      "title": "Initial Screen",
      "status": "scheduled",
      "scheduled_at": "...",
      "company_name": "Tech Corp",
      "student_name": "John Doe",
      "..."
    }
  ]
}
```

**Response Status Codes:**
200 OK | 401 Unauthorized

---
### POST /api/interviews/
**Description:** Schedule a new interview for a specific application.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Employer only (Owner of Job)

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| application_id | uuid | Yes | ID of the application |
| title | string | Yes | |
| description | text | No | |
| interview_type | string | Yes | video | in_person | phone |
| scheduled_at | datetime | Yes | Future date |
| duration_minutes | integer | Yes | Default: 30 |
| location | string | No | Required if in_person |
| meeting_link | url | No | Required if video |

**Example Response (Success):**
```json
{ "id": "uuid", "status": "scheduled", "..." }
```

**Response Status Codes:**
201 Created | 400 Validation error | 403 Forbidden

---
### GET /api/interviews/<uuid:pk>/
**Description:** Retrieve detail for a single interview.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Participant (Employer or Student)

**Example Response (Success):**
```json
{ "id": "uuid", "meeting_link": "...", "..." }
```

**Response Status Codes:**
200 OK | 401 Unauthorized | 403 Forbidden | 404 Not found

---
### PATCH /api/interviews/<uuid:pk>/
**Description:** Update or reschedule an interview.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Employer only (Owner)

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | No | |
| scheduled_at | datetime | No | |
| status | string | No | confirmed | cancelled | no_show | completed |
| cancellation_reason | string | No | Required if status set to cancelled |

**Response Status Codes:**
200 OK | 400 Validation error | 403 Forbidden

---
### POST /api/interviews/<uuid:pk>/confirm/
**Description:** Student confirms attendance for a scheduled interview.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Student only (Participant)

**Request Body:** None

**Example Response (Success):**
```json
{ "message": "Interview confirmed.", "status": "confirmed" }
```

**Response Status Codes:**
200 OK | 400 Validation error | 403 Forbidden

---
### POST /api/interviews/<uuid:pk>/feedback/
**Description:** Employer submits post-interview feedback and ratings.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Employer only (Owner)

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| rating | integer | Yes | 1-5 |
| technical_rating | integer | Yes | 1-5 |
| communication_rating | integer | Yes | 1-5 |
| cultural_fit_rating | integer | Yes | 1-5 |
| strengths | text | No | |
| weaknesses | text | No | |
| recommendation | string | Yes | strong_hire | hire | hesitant | reject |

**Response Status Codes:**
201 Created | 400 Validation error | 403 Forbidden

---
### GET /api/interviews/upcoming/
**Description:** List upcoming interviews for the next 7 days.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated

**Example Response (Success):**
```json
{ "count": 2, "results": [...] }
```

**Response Status Codes:**
200 OK | 401 Unauthorized
