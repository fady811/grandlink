# Billing API Documentation
Base URL: /api/billing/
Authentication: All endpoints use JWT Bearer Token unless marked as Public.

---
### GET /api/billing/plans/
**Description:** List all active subscription plans available for employers.
**Authentication:** Public
**Permissions:** AllowAny

**Example Response (Success):**
```json
[
  {
    "id": "uuid",
    "name": "Standard",
    "price_monthly": 29.99,
    "max_active_jobs": 10,
    "can_feature_jobs": true,
    "has_ats_access": false
  }
]
```

**Response Status Codes:**
200 OK

---
### GET /api/billing/my-subscription/
**Description:** Retrieve the current authenticated employer's subscription status.
**Authentication:** JWT — Authorization: Bearer <token>
**Permissions:** Authenticated | Employer only

**Example Response (Success):**
```json
{
  "id": "uuid",
  "status": "active",
  "plan_details": { "name": "Premium", "..." },
  "days_remaining": 15,
  "auto_renew": true
}
```

**Response Status Codes:**
200 OK | 403 Forbidden | 401 Unauthorized
