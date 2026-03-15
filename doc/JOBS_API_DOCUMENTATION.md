# GradLink Jobs Module — API Documentation

Comprehensive API reference for the Jobs, Applications, and Saved Jobs endpoints.

**Base URL:** `/api/jobs/`
**Authentication:** All endpoints require `Authorization: Bearer <access_token>` header.

---

## 💼 Jobs

### **List Jobs**

* **Path:** `/api/jobs/`
* **Method:** `GET`
* **Auth Required:** `Yes`
* **Permission:** Any authenticated user
* **Description:** Returns a paginated list of all **active** job postings. Supports search, filtering, and ordering.

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `page` | integer | Page number (default: 1) |
| `page_size` | integer | Items per page (default: 20, max: 100) |
| `search` | string | Search in title, description, location, company name |
| `work_type` | string | Filter: `full_time`, `part_time`, `internship`, `contract`, `remote` |
| `experience_level` | string | Filter: `entry`, `mid`, `senior`, `fresh_grad` |
| `is_remote` | boolean | Filter: `true` or `false` |
| `location` | string | Filter by location (partial match) |
| `skills` | string | Filter by skill IDs (comma-separated, e.g. `1,3,5`) |
| `salary_min` | decimal | Minimum salary filter |
| `salary_max` | decimal | Maximum salary filter |
| `ordering` | string | Sort by: `created_at`, `-created_at`, `deadline`, `salary_min`, `salary_max`, `views_count` |

**Example Request:**

```
GET /api/jobs/?work_type=internship&experience_level=fresh_grad&search=python&page=1&page_size=10
```

**Success Response (200 OK):**

```json
{
  "count": 45,
  "total_pages": 5,
  "current_page": 1,
  "page_size": 10,
  "next": "http://localhost:8000/api/jobs/?page=2",
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "title": "Junior Python Developer",
      "company_name": "TechCorp",
      "company_logo": null,
      "location": "Cairo, Egypt",
      "is_remote": false,
      "work_type": "full_time",
      "experience_level": "entry",
      "salary_min": "5000.00",
      "salary_max": "8000.00",
      "hide_salary": false,
      "skills": [
        { "id": 1, "name": "Python", "category": "technical" },
        { "id": 2, "name": "Django", "category": "technical" }
      ],
      "status": "active",
      "deadline": "2026-04-01T00:00:00Z",
      "applications_count": 12,
      "views_count": 340,
      "is_expired": false,
      "is_saved": true,
      "created_at": "2026-02-28T10:00:00Z"
    }
  ]
}
```

> **Note:** If `hide_salary` is `true`, both `salary_min` and `salary_max` will return `null`.

---

### **Create Job**

* **Path:** `/api/jobs/`
* **Method:** `POST`
* **Auth Required:** `Yes`
* **Permission:** `Employer only`
* **Description:** Creates a new job posting. The employer is automatically set from the authenticated user's profile.

**Request Body:**

```json
{
  "title": "string (min 3 chars, required)",
  "description": "string (min 20 chars, required)",
  "requirements": "string (optional)",
  "responsibilities": "string (optional)",
  "work_type": "string (full_time|part_time|internship|contract|remote, default: full_time)",
  "experience_level": "string (entry|mid|senior|fresh_grad, default: entry)",
  "skill_ids": [1, 2, 3],
  "location": "string (optional)",
  "is_remote": "boolean (default: false)",
  "salary_min": "decimal (optional, >= 0)",
  "salary_max": "decimal (optional, >= salary_min)",
  "hide_salary": "boolean (default: false)",
  "status": "string (draft|active|paused|closed, default: draft)",
  "deadline": "iso-datetime (optional, must be in the future)"
}
```

**Example Request:**

```json
{
  "title": "Frontend React Developer",
  "description": "We are looking for a talented React developer to join our team and build modern web applications.",
  "requirements": "2+ years experience with React, TypeScript, and REST APIs.",
  "responsibilities": "Build and maintain frontend components, collaborate with the design team.",
  "work_type": "full_time",
  "experience_level": "mid",
  "skill_ids": [1, 5, 8],
  "location": "Cairo, Egypt",
  "is_remote": true,
  "salary_min": 10000,
  "salary_max": 15000,
  "status": "active",
  "deadline": "2026-05-01T00:00:00Z"
}
```

**Success Response (201 Created):**

```json
{
  "id": "a1b2c3d4-...",
  "title": "Frontend React Developer",
  "description": "We are looking for...",
  "requirements": "2+ years experience...",
  "responsibilities": "Build and maintain...",
  "work_type": "full_time",
  "experience_level": "mid",
  "skills": [
    { "id": 1, "name": "React", "category": "technical" },
    { "id": 5, "name": "TypeScript", "category": "technical" }
  ],
  "location": "Cairo, Egypt",
  "is_remote": true,
  "salary_min": "10000.00",
  "salary_max": "15000.00",
  "hide_salary": false,
  "status": "active",
  "deadline": "2026-05-01T00:00:00Z",
  "company_name": "TechCorp",
  "company_industry": "Technology",
  "company_size": "11-50",
  "company_website": "https://techcorp.com",
  "is_verified_employer": true,
  "applications_count": 0,
  "views_count": 0,
  "is_expired": false,
  "is_saved": false,
  "created_at": "2026-02-28T17:20:00Z",
  "updated_at": "2026-02-28T17:20:00Z"
}
```

**Error Response (400 Bad Request):**

```json
{
  "title": ["Job title must be at least 3 characters."],
  "salary_min": ["Minimum salary cannot exceed maximum salary."],
  "deadline": ["Deadline cannot be in the past."]
}
```

**Error Response (403 Forbidden):**

```json
{ "detail": "Only employers can perform this action." }
```

---

### **Retrieve Job Details**

* **Path:** `/api/jobs/<uuid:id>/`
* **Method:** `GET`
* **Auth Required:** `Yes`
* **Permission:** Any authenticated user
* **Description:** Returns full job details. **Automatically increments `views_count`** on each request.

**Success Response (200 OK):**

Same structure as Create Job response above, with full company info included.

---

### **Update Job**

* **Path:** `/api/jobs/<uuid:id>/`
* **Method:** `PUT` (full) or `PATCH` (partial)
* **Auth Required:** `Yes`
* **Permission:** `Employer who owns the job only`
* **Description:** Update a job posting. Only the employer who created the job can modify it.

**Example PATCH Request:**

```json
{
  "status": "paused",
  "salary_max": 20000
}
```

---

### **Delete Job**

* **Path:** `/api/jobs/<uuid:id>/`
* **Method:** `DELETE`
* **Auth Required:** `Yes`
* **Permission:** `Employer who owns the job only`
* **Description:** Permanently deletes a job posting and all associated applications.

**Success Response (204 No Content):**

*(No body)*

---

### **My Jobs (Employer Dashboard)**

* **Path:** `/api/jobs/my-jobs/`
* **Method:** `GET`
* **Auth Required:** `Yes`
* **Permission:** `Employer only`
* **Description:** Returns all jobs posted by the authenticated employer (**all statuses**: draft, active, paused, closed, expired).

**Success Response (200 OK):**

Same paginated structure as List Jobs.

---

## 📝 Applications

### **Apply to Job**

* **Path:** `/api/jobs/<uuid:job_id>/apply/`
* **Method:** `POST`
* **Auth Required:** `Yes`
* **Permission:** `Student only`
* **Content-Type:** `multipart/form-data` (if uploading resume) or `application/json`
* **Description:** Submit an application for a job. Each student can apply **only once** per job.

**Request Body:**

```json
{
  "cover_letter": "string (optional)",
  "resume": "file (optional, PDF or Word, max 5MB)"
}
```

**Success Response (201 Created):**

```json
{
  "id": "uuid",
  "cover_letter": "I am excited to apply...",
  "resume": "/media/applications/resumes/my_cv.pdf",
  "applied_at": "2026-02-28T17:30:00Z"
}
```

**Error Responses:**

```json
// 400 — Job not active
{ "error": "This job is no longer accepting applications." }

// 400 — Job expired
{ "error": "This job posting has expired." }

// 409 — Duplicate application
{ "error": "You have already applied to this job." }

// 403 — Not a student
{ "detail": "Only students can perform this action." }
```

---

### **My Applications (Student)**

* **Path:** `/api/jobs/my-applications/`
* **Method:** `GET`
* **Auth Required:** `Yes`
* **Permission:** `Student only`
* **Description:** Returns all applications submitted by the authenticated student.

**Success Response (200 OK):**

```json
{
  "count": 5,
  "total_pages": 1,
  "current_page": 1,
  "page_size": 20,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "job_id": "uuid",
      "job_title": "Frontend React Developer",
      "company_name": "TechCorp",
      "student_email": "student@example.com",
      "student_name": "Ahmed Mohamed",
      "student_university": "Cairo University",
      "status": "pending",
      "applied_at": "2026-02-28T17:30:00Z",
      "updated_at": "2026-02-28T17:30:00Z"
    }
  ]
}
```

---

### **Job Applications (Employer)**

* **Path:** `/api/jobs/<uuid:job_id>/applications/`
* **Method:** `GET`
* **Auth Required:** `Yes`
* **Permission:** `Employer who owns the job`
* **Description:** Returns all applications for a specific job. Supports filtering by status.

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `status` | string | Filter: `pending`, `reviewing`, `shortlisted`, `interview`, `accepted`, `rejected`, `withdrawn` |

**Example Request:**

```
GET /api/jobs/a1b2c3d4-.../applications/?status=pending
```

**Success Response (200 OK):**

Same paginated structure as My Applications. Returns empty list if the employer doesn't own the job.

---

### **Application Detail**

* **Path:** `/api/jobs/applications/<uuid:id>/`
* **Method:** `GET`
* **Auth Required:** `Yes`
* **Permission:** `Student who applied` **or** `Employer who owns the job` **or** `Admin`
* **Description:** Returns full application details including cover letter and resume.

**Success Response (200 OK):**

```json
{
  "id": "uuid",
  "job_id": "uuid",
  "job_title": "Frontend React Developer",
  "company_name": "TechCorp",
  "student_id": "uuid",
  "student_email": "student@example.com",
  "student_name": "Ahmed Mohamed",
  "cover_letter": "I am excited to apply for this position...",
  "resume": "/media/applications/resumes/my_cv.pdf",
  "status": "reviewing",
  "employer_notes": "Strong candidate, schedule interview",
  "applied_at": "2026-02-28T17:30:00Z",
  "updated_at": "2026-03-01T09:00:00Z"
}
```

> **Note:** The `employer_notes` field is **only visible to employers**. Students will not see this field in the response.

---

### **Update Application Status (Employer)**

* **Path:** `/api/jobs/applications/<uuid:id>/status/`
* **Method:** `PATCH`
* **Auth Required:** `Yes`
* **Permission:** `Employer who owns the job`
* **Description:** Employer updates the application status and/or adds private notes.

**Request Body:**

```json
{
  "status": "string (pending|reviewing|shortlisted|interview|accepted|rejected)",
  "employer_notes": "string (optional, private)"
}
```

**Example Request:**

```json
{
  "status": "shortlisted",
  "employer_notes": "Strong Python skills, matches job requirements well."
}
```

**Success Response (200 OK):**

```json
{
  "status": "shortlisted",
  "employer_notes": "Strong Python skills, matches job requirements well."
}
```

**Error Response (400):**

```json
{ "status": ["Employers cannot withdraw applications. Only students can."] }
```

---

### **Withdraw Application (Student)**

* **Path:** `/api/jobs/applications/<uuid:id>/withdraw/`
* **Method:** `DELETE`
* **Auth Required:** `Yes`
* **Permission:** `Student who applied`
* **Description:** Student withdraws their application. Only allowed when status is `pending` or `reviewing`.

**Success Response (200 OK):**

```json
{ "message": "Application withdrawn successfully." }
```

**Error Response (400):**

```json
{ "error": "Cannot withdraw an application with status \"Shortlisted\"." }
```

---

## ⭐ Saved Jobs

### **List Saved Jobs**

* **Path:** `/api/jobs/saved/`
* **Method:** `GET`
* **Auth Required:** `Yes`
* **Permission:** `Student only`
* **Description:** Returns all jobs bookmarked by the authenticated student.

**Success Response (200 OK):**

```json
{
  "count": 3,
  "total_pages": 1,
  "current_page": 1,
  "page_size": 20,
  "next": null,
  "previous": null,
  "results": [
    {
      "id": "uuid",
      "job": {
        "id": "uuid",
        "title": "Junior Python Developer",
        "company_name": "TechCorp",
        "location": "Cairo",
        "work_type": "full_time",
        "experience_level": "entry",
        "salary_min": "5000.00",
        "salary_max": "8000.00",
        "status": "active",
        "is_saved": true,
        "created_at": "2026-02-28T10:00:00Z"
      },
      "saved_at": "2026-02-28T18:00:00Z"
    }
  ]
}
```

---

### **Save Job**

* **Path:** `/api/jobs/<uuid:job_id>/save/`
* **Method:** `POST`
* **Auth Required:** `Yes`
* **Permission:** `Student only`
* **Description:** Bookmark a job for later. No request body needed.

**Success Response (201 Created):**

```json
{ "message": "Job saved successfully." }
```

**Error Response (409 Conflict):**

```json
{ "error": "Job already saved." }
```

---

### **Unsave Job**

* **Path:** `/api/jobs/<uuid:job_id>/unsave/`
* **Method:** `DELETE`
* **Auth Required:** `Yes`
* **Permission:** `Student only`
* **Description:** Remove a job from bookmarks.

**Success Response (200 OK):**

```json
{ "message": "Job unsaved successfully." }
```

**Error Response (404 Not Found):**

```json
{ "error": "Job was not saved." }
```

---

## 🔧 Skills

### **List Skills**

* **Path:** `/api/jobs/skills/`
* **Method:** `GET`
* **Auth Required:** `Yes`
* **Permission:** Any authenticated user
* **Description:** Returns all available skills. Useful for autocomplete dropdowns in forms. **Not paginated** for dropdown convenience.

**Query Parameters:**

| Parameter | Type | Description |
|---|---|---|
| `search` | string | Search skills by name |

**Example Request:**

```
GET /api/jobs/skills/?search=python
```

**Success Response (200 OK):**

```json
[
  { "id": 1, "name": "Python", "category": "technical" },
  { "id": 2, "name": "Python Flask", "category": "technical" }
]
```

---

## 📊 Application Status Flow

```
┌─────────┐     ┌───────────┐     ┌──────────────┐     ┌───────────┐
│ PENDING  │────▶│ REVIEWING │────▶│ SHORTLISTED  │────▶│ INTERVIEW │
└─────────┘     └───────────┘     └──────────────┘     └───────────┘
     │               │                   │                    │
     │               │                   │                    │
     ▼               ▼                   ▼                    ▼
┌───────────┐   ┌───────────┐     ┌───────────┐        ┌──────────┐
│ WITHDRAWN │   │ REJECTED  │     │ REJECTED  │        │ ACCEPTED │
│(by student)│   │           │     │           │        │          │
└───────────┘   └───────────┘     └───────────┘        └──────────┘
```

| Status | Set By | Description |
|---|---|---|
| `pending` | System | Default when student applies |
| `reviewing` | Employer | Employer is reviewing the application |
| `shortlisted` | Employer | Candidate is shortlisted |
| `interview` | Employer | Interview has been scheduled |
| `accepted` | Employer | Candidate is accepted for the position |
| `rejected` | Employer | Application is rejected |
| `withdrawn` | Student | Student withdrew the application |

---

## 📝 Status Codes

| Code | Description |
|---|---|
| 200 | OK (Success) |
| 201 | Created (Job/Application/SavedJob created) |
| 204 | No Content (Deleted successfully) |
| 400 | Bad Request (Validation Error / Business Rule Violation) |
| 401 | Unauthorized (Missing/Invalid Token) |
| 403 | Forbidden (Wrong role or not owner) |
| 404 | Not Found |
| 409 | Conflict (Duplicate application or already saved) |
| 500 | Internal Server Error |

---

## 🔑 Permission Summary

| Endpoint | Student | Employer | Admin |
|---|---|---|---|
| List Jobs | ✅ | ✅ | ✅ |
| Create Job | ❌ | ✅ | ✅ |
| View Job Detail | ✅ | ✅ | ✅ |
| Update/Delete Job | ❌ | ✅ (owner) | ✅ |
| My Jobs | ❌ | ✅ | ❌ |
| Apply to Job | ✅ | ❌ | ❌ |
| My Applications | ✅ | ❌ | ❌ |
| Job Applications | ❌ | ✅ (owner) | ✅ |
| Application Detail | ✅ (own) | ✅ (owner) | ✅ |
| Update App Status | ❌ | ✅ (owner) | ✅ |
| Withdraw Application | ✅ (own) | ❌ | ❌ |
| Save/Unsave Job | ✅ | ❌ | ❌ |
| List Saved Jobs | ✅ | ❌ | ❌ |
| List Skills | ✅ | ✅ | ✅ |
