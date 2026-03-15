# Notifications API Documentation
Base URL: /api/notifications/
Authentication: All endpoints use JWT Bearer Token unless marked as Public.

---
### GET /api/notifications/
**Description:** List notifications for the authenticated user (Unread first, then by date).
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated

**Example Response (Success):**
```json
{
  "count": 20,
  "results": [
    {
      "id": "uuid",
      "type": "application_status_changed",
      "message": "Your application status was updated to shortlisted.",
      "is_read": false,
      "created_at": "..."
    }
  ]
}
```

**Response Status Codes:**
200 OK | 401 Unauthorized

---
### GET /api/notifications/unread-count/
**Description:** Returns the total count of unread notifications.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated

**Example Response (Success):**
```json
{ "unread_count": 5 }
```

**Response Status Codes:**
200 OK

---
### PATCH /api/notifications/<uuid:pk>/read/
**Description:** Mark a single notification as read.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated (Owner)

**Request Body:** None

**Example Response (Success):**
```json
{ "message": "Notification marked as read.", "id": "uuid" }
```

**Response Status Codes:**
200 OK | 404 Not found

---
### POST /api/notifications/mark-all-read/
**Description:** Mark all unread notifications for the authenticated user as read.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated

**Request Body:** None

**Example Response (Success):**
```json
{ "message": "5 notifications marked as read.", "count": 5 }
```

**Response Status Codes:**
200 OK
