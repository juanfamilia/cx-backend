# SIETE CX - API REFERENCE DOCUMENTATION

**Version:** 1.0  
**Base URL:** `https://cx-api.sieteic.com/api/v1`  
**Last Updated:** January 2025

---

## TABLE OF CONTENTS

1. [Authentication](#1-authentication)
2. [Users](#2-users)
3. [Companies](#3-companies)
4. [Campaigns](#4-campaigns)
5. [Evaluations](#5-evaluations)
6. [Evaluation Analysis](#6-evaluation-analysis)
7. [Prompt Manager](#7-prompt-manager-new)
8. [Dashboard](#8-dashboard)
9. [Surveys](#9-surveys)
10. [Zones](#10-zones)
11. [Notifications](#11-notifications)
12. [Payments](#12-payments)
13. [Cloudflare Integration](#13-cloudflare-integration)
14. [Error Handling](#14-error-handling)

---

## 1. AUTHENTICATION

### 1.1 Login

**Endpoint:** `POST /auth/login`

**Description:** Authenticate user and receive JWT token

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:** `200 OK`
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "first_name": "John",
    "last_name": "Doe",
    "role": 1,
    "company_id": 5
  }
}
```

**Error Responses:**
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account disabled or payment issue

---

### 1.2 Register

**Endpoint:** `POST /auth/register`

**Description:** Create new user account

**Request Body:**
```json
{
  "email": "newuser@example.com",
  "password": "securepassword",
  "first_name": "Jane",
  "last_name": "Smith",
  "role": 3,
  "company_id": 5,
  "gender": "female",
  "birthdate": "1990-05-15T00:00:00",
  "civil_status": "soltero",
  "socioeconomic": "medio"
}
```

**Response:** `201 Created`
```json
{
  "id": 123,
  "email": "newuser@example.com",
  "first_name": "Jane",
  "last_name": "Smith",
  "role": 3,
  "company_id": 5,
  "created_at": "2025-01-30T10:00:00"
}
```

---

### 1.3 Get Current User

**Endpoint:** `GET /auth/me`

**Headers:** `Authorization: Bearer {token}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": 1,
  "company_id": 5,
  "company": {
    "id": 5,
    "name": "Acme Corp",
    "email": "contact@acme.com"
  }
}
```

---

## 2. USERS

### 2.1 List Users

**Endpoint:** `GET /users`

**Headers:** `Authorization: Bearer {token}`

**Query Parameters:**
- `offset` (int): Pagination offset (default: 0)
- `limit` (int): Page size (default: 10, max: 50)
- `search` (string): Search by name or email
- `role` (int): Filter by role (0-3)

**Permissions:** Roles 0, 1, 2

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 1,
      "email": "user@example.com",
      "first_name": "John",
      "last_name": "Doe",
      "role": 1,
      "company_id": 5,
      "created_at": "2025-01-01T00:00:00"
    }
  ],
  "pagination": {
    "total": 100,
    "offset": 0,
    "limit": 10
  }
}
```

---

### 2.2 Get User by ID

**Endpoint:** `GET /users/{user_id}`

**Response:** `200 OK`
```json
{
  "id": 1,
  "email": "user@example.com",
  "first_name": "John",
  "last_name": "Doe",
  "role": 1,
  "company_id": 5,
  "gender": "male",
  "birthdate": "1985-03-20T00:00:00",
  "civil_status": "casado",
  "socioeconomic": "alto",
  "company": {
    "id": 5,
    "name": "Acme Corp"
  }
}
```

---

### 2.3 Create User

**Endpoint:** `POST /users`

**Permissions:** Roles 0, 1

**Request Body:**
```json
{
  "email": "newemployee@example.com",
  "password": "securepassword",
  "first_name": "Maria",
  "last_name": "Garcia",
  "role": 3,
  "company_id": 5,
  "gender": "female"
}
```

**Response:** `201 Created`

---

### 2.4 Update User

**Endpoint:** `PUT /users/{user_id}`

**Permissions:** Roles 0, 1

**Request Body:** (partial update)
```json
{
  "first_name": "Maria Updated",
  "role": 2
}
```

**Response:** `200 OK`

---

### 2.5 Delete User

**Endpoint:** `DELETE /users/{user_id}`

**Permissions:** Roles 0, 1

**Response:** `200 OK`
```json
{
  "message": "User deleted"
}
```

---

## 3. COMPANIES

### 3.1 List Companies

**Endpoint:** `GET /companies`

**Permissions:** Role 0 (Superadmin only)

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 1,
      "name": "Acme Corp",
      "email": "contact@acme.com",
      "phone": "+1234567890",
      "address": "123 Main St",
      "state": "New York",
      "country": "US",
      "created_at": "2025-01-01T00:00:00"
    }
  ],
  "pagination": {
    "total": 50,
    "offset": 0,
    "limit": 10
  }
}
```

---

### 3.2 Create Company

**Endpoint:** `POST /companies`

**Permissions:** Role 0

**Request Body:**
```json
{
  "name": "New Company Inc",
  "email": "info@newcompany.com",
  "phone": "+1987654321",
  "address": "456 Business Ave",
  "state": "California",
  "country": "US"
}
```

**Response:** `201 Created`

---

## 4. CAMPAIGNS

### 4.1 List Campaigns

**Endpoint:** `GET /campaigns`

**Query Parameters:**
- `offset`, `limit`: Pagination
- `search`: Search by name
- `status`: Filter by status

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 10,
      "name": "Q1 2025 Mystery Shopping",
      "description": "Banking branch evaluation campaign",
      "start_date": "2025-01-01T00:00:00",
      "end_date": "2025-03-31T23:59:59",
      "company_id": 5,
      "created_at": "2024-12-15T00:00:00"
    }
  ],
  "pagination": {
    "total": 25,
    "offset": 0,
    "limit": 10
  }
}
```

---

### 4.2 Create Campaign

**Endpoint:** `POST /campaigns`

**Permissions:** Roles 0, 1

**Request Body:**
```json
{
  "name": "Q2 2025 Campaign",
  "description": "Retail store evaluations",
  "start_date": "2025-04-01T00:00:00",
  "end_date": "2025-06-30T23:59:59",
  "company_id": 5
}
```

**Response:** `201 Created`

---

### 4.3 Assign Users to Campaign

**Endpoint:** `POST /campaign-assignments/users`

**Request Body:**
```json
{
  "campaign_id": 10,
  "user_ids": [15, 16, 17]
}
```

**Response:** `200 OK`

---

### 4.4 Assign Zones to Campaign

**Endpoint:** `POST /campaign-assignments/zones`

**Request Body:**
```json
{
  "campaign_id": 10,
  "zone_ids": [3, 4, 5]
}
```

**Response:** `200 OK`

---

## 5. EVALUATIONS

### 5.1 List Evaluations

**Endpoint:** `GET /evaluations`

**Query Parameters:**
- `offset`, `limit`: Pagination
- `filter`: Status filter (pending, analyzing, completed)
- `search`: Search by location or collaborator

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 100,
      "campaigns_id": 10,
      "user_id": 15,
      "video_id": 200,
      "location": "Branch Downtown NYC",
      "evaluated_collaborator": "John Smith",
      "status": "completed",
      "created_at": "2025-01-20T14:30:00",
      "video": {
        "id": 200,
        "url": "https://customer-stream.cloudflarestream.com/abc123",
        "title": "Mystery Shop - Branch 01"
      }
    }
  ],
  "pagination": {
    "total": 150,
    "offset": 0,
    "limit": 10
  }
}
```

---

### 5.2 Get Evaluation by ID

**Endpoint:** `GET /evaluations/{evaluation_id}`

**Response:** `200 OK`
```json
{
  "id": 100,
  "campaigns_id": 10,
  "user_id": 15,
  "video_id": 200,
  "location": "Branch Downtown NYC",
  "evaluated_collaborator": "John Smith",
  "status": "completed",
  "evaluation_answers": [
    {
      "question_id": 1,
      "answer": "Excellent service provided"
    }
  ],
  "campaign": {
    "id": 10,
    "name": "Q1 2025 Mystery Shopping"
  },
  "video": {
    "url": "https://customer-stream.cloudflarestream.com/abc123"
  },
  "created_at": "2025-01-20T14:30:00"
}
```

---

### 5.3 Submit Evaluation

**Endpoint:** `POST /evaluations`

**Permissions:** Role 3 (Shopper)

**Content-Type:** `multipart/form-data`

**Form Fields:**
- `media_url` (string): Cloudflare Stream video UID
- `video_title` (string): Title for the video
- `campaign_id` (int): Campaign ID
- `location` (string, optional): Physical location
- `evaluated_collaborator` (string, optional): Employee name
- `evaluation_answers` (JSON string): Survey answers

**Request Example:**
```
POST /evaluations
Content-Type: multipart/form-data

media_url=abc123def456
video_title=Branch Visit - Jan 20
campaign_id=10
location=Branch Downtown NYC
evaluated_collaborator=John Smith
evaluation_answers=[{"question_id":1,"answer":"Excellent"}]
```

**Response:** `201 Created`
```json
{
  "id": 100,
  "campaigns_id": 10,
  "user_id": 15,
  "video_id": 200,
  "status": "pending",
  "created_at": "2025-01-20T14:30:00",
  "message": "Evaluation created. AI analysis in progress."
}
```

**Background Process:**
1. Video download from Cloudflare Stream
2. Audio extraction (MoviePy)
3. Transcription (OpenAI Whisper)
4. Dual analysis (GPT-4o with company-specific prompt)
5. Results stored in `evaluation_analysis` table
6. Status updated to "completed"

---

### 5.4 Change Evaluation Status

**Endpoint:** `PUT /evaluations/status/{evaluation_id}`

**Permissions:** Roles 1, 2

**Request Body:**
```json
{
  "status": "approved"
}
```

**Response:** `200 OK`

---

## 6. EVALUATION ANALYSIS

### 6.1 Get Analysis for Evaluation

**Endpoint:** `GET /evaluation-analysis/{evaluation_id}`

**Permissions:** Roles 0, 1, 2

**Response:** `200 OK`
```json
{
  "id": 50,
  "evaluation_id": 100,
  "analysis": "Full GPT-4o response text...",
  "executive_view": "# Vista Ejecutiva\n\n1. 🧾 Resumen ejecutivo:\nInteracción positiva con oportunidades de mejora en tiempo de respuesta...",
  "operative_view": "{\"IOC\":{\"score\":75,\"justificacion\":\"...\"},\"IRD\":{\"score\":20,...}}",
  "created_at": "2025-01-20T14:35:00"
}
```

**Executive View Format:** Markdown text with emojis, bullets, structured insights

**Operative View Format:** JSON string with KPIs:
```json
{
  "id_entrevista": "eval_100",
  "timestamp_analisis": "2025-01-20 14:35:00",
  "IOC": {
    "score": 75,
    "justificacion": "Oportunidad identificada correctamente"
  },
  "IRD": {
    "score": 20,
    "justificacion": "Cliente satisfecho, sin riesgo de deserción"
  },
  "CES": {
    "score": 15,
    "justificacion": "Proceso fluido con mínimo esfuerzo"
  },
  "Calidad": {
    "saludo": true,
    "identificacion": true,
    "ofrecimiento": true,
    "cierre": true,
    "valor_agregado": false
  },
  "Verbatims": {
    "positivos": [
      "\"Excelente atención, muy amable\" - Cliente (01:30)"
    ],
    "negativos": [],
    "criticos": []
  },
  "acciones_sugeridas": [
    "Reforzar entrenamiento en valor agregado"
  ]
}
```

---

## 7. PROMPT MANAGER (NEW)

### 7.1 List Company Prompts

**Endpoint:** `GET /prompts`

**Permissions:** Roles 0, 1

**Query Parameters:**
- `offset`, `limit`: Pagination

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 1,
      "company_id": 5,
      "prompt_name": "Banking CX Analysis",
      "prompt_type": "dual_analysis",
      "system_prompt": "Eres un analista especializado en banca...",
      "is_active": true,
      "metadata": {
        "temperature": 0.7,
        "max_tokens": 4000
      },
      "created_at": "2025-01-15T00:00:00"
    }
  ],
  "total": 5
}
```

---

### 7.2 Create Custom Prompt

**Endpoint:** `POST /prompts`

**Permissions:** Roles 0, 1

**Request Body:**
```json
{
  "company_id": 5,
  "prompt_name": "Retail CX Analysis",
  "prompt_type": "dual_analysis",
  "system_prompt": "Eres un analista especializado en experiencia retail. Evalúa aspectos como atención al cliente, merchandising, tiempo de espera...",
  "is_active": true,
  "metadata": {
    "temperature": 0.7,
    "industry": "retail"
  }
}
```

**Response:** `201 Created`

**Note:** Setting `is_active: true` will automatically deactivate other prompts of the same type for that company.

---

### 7.3 Update Prompt

**Endpoint:** `PUT /prompts/{prompt_id}`

**Request Body:** (partial update)
```json
{
  "system_prompt": "Updated prompt text...",
  "is_active": true
}
```

**Response:** `200 OK`

---

### 7.4 Delete Prompt

**Endpoint:** `DELETE /prompts/{prompt_id}`

**Response:** `200 OK`
```json
{
  "message": "Prompt deleted successfully"
}
```

---

## 8. DASHBOARD

### 8.1 Get Dashboard Summary

**Endpoint:** `GET /dashboard`

**Headers:** `Authorization: Bearer {token}`

**Description:** Returns role-specific dashboard data

**Permissions:** All roles (0, 1, 2, 3)

**Response varies by role:**

#### **Role 0 (Superadmin):**
```json
{
  "total_companies": 50,
  "total_users": 1200,
  "total_evaluations": 5000,
  "evaluations_this_month": 450,
  "active_campaigns": 25,
  "companies_summary": [
    {
      "company_id": 1,
      "company_name": "Acme Corp",
      "total_evaluations": 150,
      "pending_evaluations": 10
    }
  ]
}
```

#### **Role 1 (Admin):**
```json
{
  "company_id": 5,
  "company_name": "Acme Corp",
  "total_users": 45,
  "total_shoppers": 30,
  "total_evaluations": 500,
  "completed_evaluations": 450,
  "pending_evaluations": 50,
  "active_campaigns": 5,
  "avg_nps": 8.5,
  "evaluations_by_month": {
    "2025-01": 150,
    "2025-02": 200
  }
}
```

#### **Role 2 (Manager):**
```json
{
  "assigned_campaigns": 3,
  "total_evaluations": 120,
  "completed_evaluations": 100,
  "pending_evaluations": 20,
  "avg_nps": 8.2
}
```

#### **Role 3 (Shopper):**
```json
{
  "total_evaluations_submitted": 25,
  "pending_evaluations": 2,
  "completed_evaluations": 23,
  "active_campaigns": 2,
  "next_assignment": {
    "campaign_id": 10,
    "campaign_name": "Q1 2025 Mystery Shopping",
    "deadline": "2025-02-15T23:59:59"
  }
}
```

---

## 9. SURVEYS

### 9.1 List Surveys

**Endpoint:** `GET /surveys`

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 1,
      "name": "Branch Evaluation Form",
      "description": "Standard form for branch visits",
      "created_at": "2024-12-01T00:00:00",
      "survey_forms": [
        {
          "id": 1,
          "question": "How was the greeting?",
          "type": "text",
          "is_required": true
        }
      ]
    }
  ]
}
```

---

### 9.2 Create Survey

**Endpoint:** `POST /surveys`

**Permissions:** Roles 0, 1

**Request Body:**
```json
{
  "name": "New Survey Form",
  "description": "Custom evaluation form",
  "survey_forms": [
    {
      "question": "Rate the service",
      "type": "rating",
      "is_required": true
    }
  ]
}
```

---

## 10. ZONES

### 10.1 List Zones

**Endpoint:** `GET /zones`

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 1,
      "name": "Zone NYC Metro",
      "country": "US",
      "state": "New York",
      "city": "New York City"
    }
  ]
}
```

---

### 10.2 Create Zone

**Endpoint:** `POST /zones`

**Permissions:** Roles 0, 1

**Request Body:**
```json
{
  "name": "Zone LA Metro",
  "country": "US",
  "state": "California",
  "city": "Los Angeles"
}
```

---

## 11. NOTIFICATIONS

### 11.1 List User Notifications

**Endpoint:** `GET /notifications`

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 50,
      "user_id": 15,
      "title": "Evaluation Analysis Complete",
      "message": "Your evaluation #100 has been analyzed by AI",
      "type": "evaluation_complete",
      "is_read": false,
      "created_at": "2025-01-20T14:35:00"
    }
  ]
}
```

---

### 11.2 Mark Notification as Read

**Endpoint:** `PUT /notifications/{notification_id}/read`

**Response:** `200 OK`

---

## 12. PAYMENTS

### 12.1 List Payments

**Endpoint:** `GET /payments`

**Permissions:** Roles 0, 1

**Response:** `200 OK`
```json
{
  "data": [
    {
      "id": 10,
      "company_id": 5,
      "amount": 500.00,
      "currency": "USD",
      "status": "paid",
      "payment_date": "2025-01-01T00:00:00",
      "next_payment_due": "2025-02-01T00:00:00"
    }
  ]
}
```

---

## 13. CLOUDFLARE INTEGRATION

### 13.1 Get Upload URL

**Endpoint:** `POST /cloudflare/stream/upload`

**Description:** Get TUS upload URL for video

**Response:** `200 OK`
```json
{
  "upload_url": "https://upload.videodelivery.net/tus/abc123",
  "video_uid": "abc123def456"
}
```

**Usage:**
1. Frontend calls this endpoint
2. Receives upload URL
3. Uses TUS protocol to upload video to Cloudflare
4. Submits evaluation with `media_url=abc123def456`

---

### 13.2 Cloudflare Webhook (Internal)

**Endpoint:** `POST /cloudflare/webhook`

**Description:** Receives video processing status from Cloudflare

**Used internally by Cloudflare Stream**

---

## 14. ERROR HANDLING

### Standard Error Response Format

```json
{
  "detail": "Error message description"
}
```

### HTTP Status Codes

| Code | Meaning                 | Description                                    |
|------|-------------------------|------------------------------------------------|
| 200  | OK                      | Request successful                             |
| 201  | Created                 | Resource created successfully                  |
| 400  | Bad Request             | Invalid request parameters                     |
| 401  | Unauthorized            | Missing or invalid authentication token        |
| 403  | Forbidden               | Insufficient permissions                       |
| 404  | Not Found               | Resource not found                             |
| 422  | Unprocessable Entity    | Validation error                               |
| 500  | Internal Server Error   | Server-side error                              |

### Common Error Examples

#### **401 Unauthorized:**
```json
{
  "detail": "Could not validate credentials"
}
```

#### **403 Forbidden:**
```json
{
  "detail": "You don't have permission to retrieve this analysis"
}
```

#### **404 Not Found:**
```json
{
  "detail": "Evaluation not found"
}
```

#### **422 Validation Error:**
```json
{
  "detail": [
    {
      "loc": ["body", "email"],
      "msg": "value is not a valid email address",
      "type": "value_error.email"
    }
  ]
}
```

---

## APPENDIX A: ROLE PERMISSIONS SUMMARY

| Endpoint                  | Superadmin (0) | Admin (1) | Manager (2) | Shopper (3) |
|---------------------------|----------------|-----------|-------------|-------------|
| POST /auth/login          | ✅             | ✅        | ✅          | ✅          |
| GET /users                | ✅             | ✅        | ✅          | ❌          |
| POST /users               | ✅             | ✅        | ❌          | ❌          |
| GET /companies            | ✅             | ❌        | ❌          | ❌          |
| POST /campaigns           | ✅             | ✅        | ❌          | ❌          |
| POST /evaluations         | ❌             | ❌        | ❌          | ✅          |
| GET /evaluation-analysis  | ✅             | ✅        | ✅          | ❌          |
| GET /prompts              | ✅             | ✅        | ❌          | ❌          |
| POST /prompts             | ✅             | ✅        | ❌          | ❌          |
| GET /dashboard            | ✅             | ✅        | ✅          | ✅          |

---

## APPENDIX B: RATE LIMITS

**Current Implementation:** No rate limits enforced

**Recommended (Future):**
- Public endpoints: 100 requests/minute
- Authenticated endpoints: 1000 requests/minute
- Video uploads: 10 uploads/hour per user

---

## APPENDIX C: PAGINATION

All list endpoints support pagination with:
- `offset` (int): Starting position (default: 0)
- `limit` (int): Page size (default: 10, max: 50)

**Response includes:**
```json
{
  "data": [...],
  "pagination": {
    "total": 500,
    "offset": 0,
    "limit": 10
  }
}
```

---

**End of API Reference Documentation**

For architecture details, see `ARCHITECTURE_MASTER.md`  
For deployment instructions, see `DEPLOYMENT.md` (Phase 5)  
For testing documentation, see `TESTING.md` (Phase 5)
