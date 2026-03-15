# Jobs API Documentation
Base URL: /api/jobs/
Authentication: All endpoints use JWT Bearer Token unless marked as Public.

---
### GET /api/jobs/categories/
**Description:** List all active job categories.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| search | string | No | Search by name or description |

**Example Response (Success):**
```json
[
  { "id": 1, "name": "Engineering", "slug": "engineering", "description": "..." }
]
```

**Response Status Codes:**
200 OK | 401 Unauthorized

---
### GET /api/jobs/skills/
**Description:** List all skills (for autocomplete/dropdowns).
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| search | string | No | Search by skill name |

**Example Response (Success):**
```json
[
  { "id": 1, "name": "Python", "category": "technical" }
]
```

**Response Status Codes:**
200 OK | 401 Unauthorized

---
### GET /api/jobs/
**Description:** List active and unflagged jobs.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| work_type | string | No | full_time | part_time | internship | contract | remote |
| experience_level | string | No | entry | mid | senior | fresh_grad |
| is_remote | boolean | No | Filter by remote status |
| location | string | No | Case-insensitive search in location field |
| category | string | No | Filter by category ID or slug |
| skills | string | No | Comma-separated list of skill IDs |
| salary_min | number | No | Filter jobs where salary_max >= value |
| salary_max | number | No | Filter jobs where salary_min <= value |
| search | string | No | Search title, description, location, company |
| ordering | string | No | created_at, deadline, salary_min, salary_max, views_count |

**Example Response (Success):**
```json
{
  "count": 100,
  "next": "...",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "title": "Backend Dev",
      "company_name": "Tech Corp",
      "location": "Remote",
      "salary_min": 50000.00,
      "salary_max": 80000.00,
      "is_featured": true,
      "..."
    }
  ]
}
```

**Response Status Codes:**
200 OK | 401 Unauthorized

---
### POST /api/jobs/
**Description:** Create a new job posting.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Employer only

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| title | string | Yes | Min 3 characters |
| description | text | Yes | Min 20 characters |
| requirements | text | No | |
| responsibilities | text | No | |
| work_type | string | Yes | full_time | part_time | internship | contract | remote |
| experience_level | string | Yes | entry | mid | senior | fresh_grad |
| skill_ids | array (int) | No | List of skill IDs |
| category_id | integer | No | Category ID |
| location | string | No | |
| is_remote | boolean | No | |
| salary_min | decimal | No | |
| salary_max | decimal | No | |
| hide_salary | boolean | No | Default: false |
| deadline | datetime | No | Future date only |

**Example Response (Success):**
```json
{ "id": "uuid", "status": "draft", "..." }
```

**Response Status Codes:**
201 Created | 400 Validation error | 403 Forbidden

---
### GET /api/jobs/my-jobs/
**Description:** Employer's own job postings with all statuses.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Employer only

**Example Response (Success):**
```json
{ "count": 5, "results": [...] }
```

**Response Status Codes:**
200 OK | 401 Unauthorized | 403 Forbidden

---
### POST /api/jobs/<uuid:pk>/submit-for-review/
**Description:** Employer submits a draft job for admin approval.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Employer only (Owner)

**Request Body:** None

**Example Response (Success):**
```json
{ "message": "Job submitted for admin review.", "job": { "..." } }
```

**Response Status Codes:**
200 OK | 400 Validation error | 403 Forbidden | 404 Not found

---
### POST /api/jobs/<uuid:job_id>/apply/
**Description:** Student applies to a job.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Student only

**Path Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| job_id | uuid | Yes | ID of the job |

**Request Headers:**
Content-Type: multipart/form-data

**Request Body (multipart/form-data):**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| cover_letter | text | No | |
| resume | file | Yes | PDF or Word, max 5MB |

**Example Response (Success):**
```json
{ "id": "uuid", "status": "pending", "applied_at": "..." }
```

**Response Status Codes:**
201 Created | 400 Validation error | 403 Forbidden | 404 Not found | 409 Conflict

---
### GET /api/jobs/<uuid:job_id>/applications/
**Description:** Employer views applications for their job.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Employer only (Owner)

**Query Parameters:**
| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| status | string | No | Filter by application status |

**Example Response (Success):**
```json
{ "count": 10, "results": [...] }
```

**Response Status Codes:**
200 OK | 401 Unauthorized | 403 Forbidden | 404 Not found

---
### PATCH /api/jobs/applications/<uuid:pk>/status/
**Description:** Employer updates application status (Shortlisted, Rejected, etc.).
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Employer only (Owner of Job)

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| status | string | Yes | reviewed | shortlisted | interview | offered | rejected |
| employer_notes | text | No | Private notes only visible to employer |

**Example Response (Success):**
```json
{ "status": "shortlisted", "..." }
```

**Response Status Codes:**
200 OK | 400 Validation error | 403 Forbidden | 404 Not found

---
### DELETE /api/jobs/applications/<uuid:pk>/withdraw/
**Description:** Student withdraws their application (sets status to withdrawn, does not delete).
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Student only (Owner)

**Request Body:** None

**Example Response (Success):**
```json
{ "message": "Application withdrawn successfully." }
```

**Response Status Codes:**
200 OK | 400 Validation error | 403 Forbidden | 404 Not found

---
### POST /api/jobs/<uuid:job_id>/save/
**Description:** Student saves/bookmarks a job.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Student only

**Example Response (Success):**
```json
{ "message": "Job saved successfully." }
```

**Response Status Codes:**
201 Created | 403 Forbidden | 404 Not found | 409 Conflict

---
### DELETE /api/jobs/<uuid:job_id>/unsave/
**Description:** Student removes a saved job.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Student only

**Example Response (Success):**
```json
{ "message": "Job unsaved successfully." }
```

**Response Status Codes:**
200 OK | 403 Forbidden | 404 Not found

---
### POST /api/jobs/<uuid:pk>/report/
**Description:** Reports a job for spam, misleading content, etc.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Not owner of the job

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| reason | string | Yes | spam | misleading | offensive | other |
| details | text | No | Additional details |

**Example Response (Success):**
```json
{ "id": "uuid", "status": "pending", "..." }
```

**Response Status Codes:**
201 Created | 401 Unauthorized | 409 Conflict
