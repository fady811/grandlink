# Support API Documentation
Base URL: /api/support/
Authentication: All endpoints use JWT Bearer Token unless marked as Public.

---
### GET /api/support/tickets/
**Description:** List own support tickets (Students/Employers) or all tickets (Admin).
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated

**Example Response (Success):**
```json
[
  {
    "id": "uuid",
    "subject": "Login issues",
    "status": "open",
    "category": "technical",
    "priority": "medium",
    "..."
  }
]
```

**Response Status Codes:**
200 OK | 401 Unauthorized

---
### POST /api/support/tickets/
**Description:** Create a new support ticket.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| subject | string | Yes | |
| message | text | Yes | |
| category | string | No | technical | account | job_posting | billing | other |
| priority | string | No | low | medium | high |

**Example Response (Success):**
```json
{ "id": "uuid", "status": "open", "..." }
```

**Response Status Codes:**
201 Created | 400 Validation error

---
### GET /api/support/tickets/<uuid:pk>/
**Description:** Retrieve a ticket's detail including all replies.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Owner or Admin

**Example Response (Success):**
```json
{
  "id": "uuid",
  "subject": "...",
  "replies": [
    { "author_email": "admin@gradlink.com", "message": "We are looking into it.", "is_staff_reply": true }
  ]
}
```

**Response Status Codes:**
200 OK | 403 Forbidden | 404 Not found

---
### POST /api/support/tickets/<uuid:pk>/reply/
**Description:** Add a reply to a support ticket.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Owner or Admin

**Request Body:**
| Field | Type | Required | Description |
|-------|------|----------|-------------|
| message | text | Yes | |

**Response Status Codes:**
201 Created | 400 Validation error | 403 Forbidden
