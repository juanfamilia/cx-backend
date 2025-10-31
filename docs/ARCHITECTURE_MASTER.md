# SIETE CX - MASTER ARCHITECTURE DOCUMENTATION

**Version:** 1.0  
**Last Updated:** January 2025  
**Product:** Siete CX - Customer Experience Intelligence Platform  
**Company:** Siete Inteligencia Creativa

---

## TABLE OF CONTENTS

1. [System Overview](#1-system-overview)
2. [Technical Stack](#2-technical-stack)
3. [Architecture Patterns](#3-architecture-patterns)
4. [Project Structure](#4-project-structure)
5. [Database Schema](#5-database-schema)
6. [API Endpoints Reference](#6-api-endpoints-reference)
7. [Authentication & Authorization](#7-authentication--authorization)
8. [AI Integration Architecture](#8-ai-integration-architecture)
9. [Data Flow](#9-data-flow)
10. [Module Descriptions](#10-module-descriptions)
11. [Naming Conventions](#11-naming-conventions)
12. [Environment Configuration](#12-environment-configuration)
13. [Deployment Architecture](#13-deployment-architecture)
14. [Integration Points](#14-integration-points)

---

## 1. SYSTEM OVERVIEW

### 1.1 Product Description

Siete CX is an enterprise-grade Customer Experience Intelligence platform that combines:
- **Video-based Mystery Shopping** evaluations
- **AI-powered dual-prompt analysis** (Executive + Operative views)
- **Multi-tenant architecture** for multiple companies
- **Campaign management** with geographical zones
- **Real-time dashboards** with role-based insights
- **Survey and evaluation** workflows

### 1.2 Core Features

- 🎥 **Video Evaluation System**: Upload and manage customer interaction videos via Cloudflare Stream
- 🤖 **AI Analysis Engine**: Whisper transcription + GPT-4o dual-analysis (Executive & Operative views)
- 📊 **Dynamic Dashboards**: Role-based KPI summaries (Superadmin, Admin, Manager, Shopper)
- 🎯 **Campaign Management**: Create campaigns with goals, assign users and zones
- 📋 **Survey System**: Custom forms with dynamic question builders
- 💳 **Payment Management**: Track company subscriptions and payment status
- 🔔 **Notification System**: In-app notifications for evaluations and campaigns
- 🌍 **Geographical Zones**: Organize evaluations by country/state/city

### 1.3 User Roles

| Role ID | Role Name   | Permissions                                      |
|---------|-------------|--------------------------------------------------|
| 0       | Superadmin  | Full system access, manage all companies         |
| 1       | Admin       | Manage company, campaigns, users, evaluations    |
| 2       | Manager     | View company data, manage assigned campaigns     |
| 3       | Shopper     | Submit evaluations, view own data                |

---

## 2. TECHNICAL STACK

### 2.1 Backend Stack

| Technology      | Version  | Purpose                                    |
|-----------------|----------|--------------------------------------------|
| Python          | 3.13+    | Core programming language                  |
| FastAPI         | 0.115+   | Async web framework                        |
| SQLModel        | 0.0.24   | ORM (combines SQLAlchemy + Pydantic)       |
| SQLAlchemy      | 2.0.41   | Database toolkit                           |
| Alembic         | 1.15+    | Database migrations                        |
| PostgreSQL      | 14+      | Primary relational database                |
| Pydantic        | 2.x      | Data validation and settings               |
| PyJWT           | 2.10+    | JWT token generation/validation            |
| Passlib+Bcrypt  | -        | Password hashing                           |
| AsyncPG         | 0.30+    | Async PostgreSQL driver                    |
| OpenAI SDK      | 1.91+    | AI transcription and analysis              |

### 2.2 Frontend Stack

| Technology      | Version  | Purpose                                    |
|-----------------|----------|--------------------------------------------|
| Angular         | 19.1     | Frontend framework                         |
| TypeScript      | 5.7      | Type-safe JavaScript                       |
| TailwindCSS     | 4.0      | Utility-first CSS framework                |
| PrimeNG         | 19.0     | UI component library                       |
| RxJS            | 7.8      | Reactive programming                       |
| JWT-Decode      | 4.0      | JWT token decoding                         |
| ngx-markdown    | 19.1     | Markdown rendering (for AI analysis)       |
| Chart.js        | -        | Data visualization (future)                |

### 2.3 Infrastructure & Services

| Service              | Purpose                                    |
|----------------------|--------------------------------------------|
| Railway.app          | Hosting platform (backend + database)      |
| Cloudflare Stream    | Video hosting and streaming                |
| Cloudflare R2        | Object storage (S3-compatible)             |
| AWS S3               | File storage (alternative/legacy)          |
| OpenAI API           | Whisper (transcription) + GPT-4o (analysis)|
| SendGrid             | Email notifications (future)               |
| Twilio               | SMS notifications (future)                 |

---

## 3. ARCHITECTURE PATTERNS

### 3.1 Backend Architecture

**Pattern:** Layered Architecture with Dependency Injection

```
┌─────────────────────────────────────────┐
│         FastAPI Application             │
│  (app/main.py - Entry Point)            │
└─────────────────────────────────────────┘
               │
               ├─► Middlewares (CORS, Auth)
               │
               ├─► Routes Layer
               │   (app/routes/*.py)
               │   - Endpoint definitions
               │   - Request validation
               │   - Response formatting
               │
               ├─► Services Layer
               │   (app/services/*.py)
               │   - Business logic
               │   - Data processing
               │   - External API calls
               │
               ├─► Models Layer
               │   (app/models/*.py)
               │   - SQLModel schemas
               │   - Database tables
               │   - Validation rules
               │
               └─► Core Layer
                   (app/core/*.py)
                   - Configuration
                   - Database connection
                   - Security utilities
```

### 3.2 Frontend Architecture

**Pattern:** Component-Based with Services & Guards

```
┌─────────────────────────────────────────┐
│         Angular Application             │
│  (main.ts - Bootstrap)                  │
└─────────────────────────────────────────┘
               │
               ├─► Guards (auth.guard.ts)
               │   - Route protection
               │
               ├─► Interceptors (jwt.interceptor.ts)
               │   - HTTP request/response handling
               │
               ├─► Services (app/services/*.ts)
               │   - API communication
               │   - State management
               │   - Business logic
               │
               ├─► Pages (app/pages/*/)
               │   - Smart components
               │   - Route components
               │
               ├─► Components (app/components/*/)
               │   - Reusable UI components
               │   - Presentation logic
               │
               └─► Interfaces (app/interfaces/*.ts)
                   - TypeScript types
                   - API contracts
```

### 3.3 Database Design Pattern

- **Multi-tenant:** All tables include `company_id` for data isolation
- **Soft Delete:** `deleted_at` timestamp instead of hard deletes
- **Audit Trail:** `created_at`, `updated_at` on all tables
- **Relationships:** Foreign keys with lazy loading via SQLModel

---

## 4. PROJECT STRUCTURE

### 4.1 Backend Structure (`cx-backend/`)

```
cx-backend/
├── alembic.ini                    # Alembic configuration
├── pyproject.toml                 # Python dependencies (uv)
├── uv.lock                        # Dependency lock file
├── .env.example                   # Environment variables template
├── docs/                          # Documentation
│   └── ARCHITECTURE_MASTER.md     # This file
│
└── app/                           # Main application
    ├── __init__.py
    ├── main.py                    # FastAPI app entry point
    │
    ├── core/                      # Core configuration
    │   ├── config.py              # Settings (Pydantic BaseSettings)
    │   ├── db.py                  # Database session management
    │   └── security.py            # JWT, password hashing
    │
    ├── models/                    # SQLModel schemas
    │   ├── user_model.py          # User entity
    │   ├── company_model.py       # Company entity
    │   ├── campaign_model.py      # Campaign entity
    │   ├── evaluation_model.py    # Evaluation entity
    │   ├── evaluation_analysis_model.py  # AI analysis results
    │   ├── survey_model.py        # Survey entity
    │   ├── zone_model.py          # Geographical zones
    │   ├── payment_model.py       # Payment tracking
    │   ├── notification_model.py  # Notifications
    │   └── ...                    # Other models
    │
    ├── routes/                    # API endpoints
    │   ├── main.py                # Router aggregator
    │   ├── auth_router.py         # Authentication (login, register)
    │   ├── user_router.py         # User CRUD
    │   ├── company_router.py      # Company CRUD
    │   ├── campaign_router.py     # Campaign management
    │   ├── evaluation_router.py   # Evaluation submission
    │   ├── evaluation_analysis_router.py  # AI analysis endpoints
    │   ├── dashboard_router.py    # Dashboard data
    │   ├── survey_router.py       # Survey management
    │   ├── zone_router.py         # Zone management
    │   ├── notification_router.py # Notification system
    │   ├── payment_router.py      # Payment management
    │   ├── cloudflare_router.py   # Cloudflare Stream/R2
    │   └── ...                    # Other routers
    │
    ├── services/                  # Business logic
    │   ├── users_services.py      # User operations
    │   ├── company_services.py    # Company operations
    │   ├── campaign_services.py   # Campaign logic
    │   ├── evaluation_services.py # Evaluation processing
    │   ├── evaluation_analysis_services.py  # Analysis parsing
    │   ├── openai_services.py     # OpenAI API integration
    │   ├── cloudflare_stream_services.py    # Video upload
    │   ├── cloudflare_rs_services.py        # R2 storage
    │   ├── extract_audio_services.py        # Audio extraction
    │   └── ...                    # Other services
    │
    ├── migrations/                # Alembic migrations
    │   ├── env.py                 # Migration environment
    │   └── versions/              # Migration scripts
    │
    ├── middlewares/               # Custom middlewares
    │
    ├── utils/                     # Utility functions
    │   ├── deps.py                # Dependency injection
    │   └── exceptions.py          # Custom exceptions
    │
    ├── types/                     # Type definitions
    │   └── pagination.py          # Pagination types
    │
    └── seeder/                    # Database seeders
```

### 4.2 Frontend Structure (`cx-frontend/`)

```
cx-frontend/
├── angular.json                   # Angular configuration
├── package.json                   # Node dependencies
├── tsconfig.json                  # TypeScript configuration
├── tailwind.config.js             # Tailwind configuration (future)
│
├── public/                        # Static assets
│   ├── favicon.ico
│   └── images/
│
└── src/
    ├── index.html                 # Main HTML
    ├── main.ts                    # Bootstrap application
    ├── styles.css                 # Global styles (Tailwind)
    │
    ├── environments/              # Environment configs
    │   ├── environment.ts
    │   └── environment.prod.ts
    │
    └── app/
        ├── app.component.ts       # Root component
        ├── app.config.ts          # App configuration
        ├── app.routes.ts          # Route definitions
        │
        ├── guards/                # Route guards
        │   └── auth.guard.ts      # Authentication guard
        │
        ├── interceptors/          # HTTP interceptors
        │   └── jwt.interceptor.ts # JWT token injection
        │
        ├── services/              # API services
        │   ├── auth.service.ts
        │   ├── users.service.ts
        │   ├── campaign.service.ts
        │   ├── evaluation.service.ts
        │   ├── evaluation-analysis.service.ts
        │   ├── dashboard.service.ts
        │   └── ...
        │
        ├── interfaces/            # TypeScript interfaces
        │   ├── user.ts
        │   ├── company.ts
        │   ├── campaign.ts
        │   ├── evaluation.ts
        │   ├── evaluation-analysis.ts
        │   └── ...
        │
        ├── pages/                 # Route pages
        │   ├── login/
        │   ├── dashboard/
        │   ├── campaign/
        │   ├── evaluation/
        │   ├── users/
        │   ├── companies/
        │   ├── work-areas/
        │   ├── survey-forms/
        │   ├── notifications/
        │   ├── payments/
        │   └── configuration/
        │
        ├── components/            # Reusable components
        │   ├── ui/                # Base UI components
        │   ├── navigation/
        │   ├── breadcrumb/
        │   ├── page-header/
        │   ├── table/
        │   ├── search-bar/
        │   ├── spinner/
        │   └── ...
        │
        ├── pipes/                 # Custom pipes
        │   ├── role.pipe.ts
        │   ├── phone.pipe.ts
        │   └── state-name.pipe.ts
        │
        ├── helpers/               # Helper functions
        │   ├── json-csv-convert.ts
        │   └── markdown-pdf-convert.ts
        │
        ├── constants/             # App constants
        │   ├── roles.constant.ts
        │   ├── genders.constant.ts
        │   └── navRoutes.constant.ts
        │
        └── types/                 # Type definitions
            ├── pagination.ts
            └── options.ts
```

---

## 5. DATABASE SCHEMA

### 5.1 Core Entities

#### **companies** (Multi-tenant root)
```sql
id              SERIAL PRIMARY KEY
name            VARCHAR NOT NULL
phone           VARCHAR
email           VARCHAR
address         VARCHAR
state           VARCHAR
country         VARCHAR DEFAULT 'DO'
created_at      TIMESTAMP DEFAULT NOW()
updated_at      TIMESTAMP DEFAULT NOW()
deleted_at      TIMESTAMP NULL
```

#### **users** (All platform users)
```sql
id              SERIAL PRIMARY KEY
role            INT NOT NULL DEFAULT 3
    -- 0: superadmin, 1: admin, 2: manager, 3: shopper
first_name      VARCHAR NOT NULL
last_name       VARCHAR NOT NULL
email           VARCHAR UNIQUE NOT NULL
hashed_password VARCHAR NOT NULL
gender          VARCHAR (male/female/other)
birthdate       TIMESTAMP
civil_status    VARCHAR (soltero/casado/divorciado/viudo/separado)
socioeconomic   VARCHAR (bajo/medio/alto)
inclusivity     VARCHAR
company_id      INT FK → companies.id
created_at      TIMESTAMP
updated_at      TIMESTAMP
deleted_at      TIMESTAMP NULL
```

#### **zones** (Geographical areas)
```sql
id              SERIAL PRIMARY KEY
name            VARCHAR NOT NULL
country         VARCHAR NOT NULL
state           VARCHAR NOT NULL
city            VARCHAR
created_at      TIMESTAMP
updated_at      TIMESTAMP
deleted_at      TIMESTAMP NULL
```

#### **campaigns** (Evaluation campaigns)
```sql
id              SERIAL PRIMARY KEY
name            VARCHAR NOT NULL
description     TEXT
start_date      TIMESTAMP
end_date        TIMESTAMP
company_id      INT FK → companies.id
created_at      TIMESTAMP
updated_at      TIMESTAMP
deleted_at      TIMESTAMP NULL
```

#### **evaluations** (Video evaluations)
```sql
id              SERIAL PRIMARY KEY
user_id         INT FK → users.id (shopper)
campaign_id     INT FK → campaigns.id
zone_id         INT FK → zones.id
video_url       VARCHAR (Cloudflare Stream URL)
status          VARCHAR (pending/analyzing/completed)
created_at      TIMESTAMP
updated_at      TIMESTAMP
deleted_at      TIMESTAMP NULL
```

#### **evaluation_analysis** (AI analysis results)
```sql
id              SERIAL PRIMARY KEY
evaluation_id   INT FK → evaluations.id
analysis        TEXT (full AI response)
executive_view  TEXT (consultive narrative)
operative_view  TEXT (JSON structured data)
created_at      TIMESTAMP
updated_at      TIMESTAMP
deleted_at      TIMESTAMP NULL
```

### 5.2 Entity Relationships

```
companies (1) ──────── (*) users
companies (1) ──────── (*) campaigns
companies (1) ──────── (*) payments

campaigns (1) ──────── (*) evaluations
campaigns (1) ──────── (*) campaign_users
campaigns (1) ──────── (*) campaign_zones

users (1) ──────────── (*) evaluations
users (1) ──────────── (*) user_zones
users (1) ──────────── (*) notifications

evaluations (1) ─────── (1) evaluation_analysis
evaluations (1) ─────── (1) video

zones (1) ──────────── (*) evaluations
zones (1) ──────────── (*) user_zones
```

---

## 6. API ENDPOINTS REFERENCE

**Base URL:** `/api/v1`

### 6.1 Authentication

| Method | Endpoint          | Description                  | Auth Required |
|--------|-------------------|------------------------------|---------------|
| POST   | `/auth/login`     | Login with email/password    | No            |
| POST   | `/auth/register`  | Register new user            | No            |
| GET    | `/auth/me`        | Get current user profile     | Yes           |

### 6.2 Users

| Method | Endpoint             | Description              | Roles         |
|--------|----------------------|--------------------------|---------------|
| GET    | `/users`             | List all users           | 0, 1, 2       |
| GET    | `/users/{id}`        | Get user by ID           | 0, 1, 2       |
| POST   | `/users`             | Create new user          | 0, 1          |
| PUT    | `/users/{id}`        | Update user              | 0, 1          |
| DELETE | `/users/{id}`        | Soft delete user         | 0, 1          |

### 6.3 Companies

| Method | Endpoint             | Description              | Roles         |
|--------|----------------------|--------------------------|---------------|
| GET    | `/companies`         | List all companies       | 0             |
| GET    | `/companies/{id}`    | Get company by ID        | 0, 1          |
| POST   | `/companies`         | Create company           | 0             |
| PUT    | `/companies/{id}`    | Update company           | 0, 1          |
| DELETE | `/companies/{id}`    | Soft delete company      | 0             |

### 6.4 Campaigns

| Method | Endpoint             | Description              | Roles         |
|--------|----------------------|--------------------------|---------------|
| GET    | `/campaigns`         | List campaigns           | 0, 1, 2       |
| GET    | `/campaigns/{id}`    | Get campaign by ID       | 0, 1, 2       |
| POST   | `/campaigns`         | Create campaign          | 0, 1          |
| PUT    | `/campaigns/{id}`    | Update campaign          | 0, 1          |
| DELETE | `/campaigns/{id}`    | Soft delete campaign     | 0, 1          |

### 6.5 Evaluations

| Method | Endpoint                | Description                  | Roles         |
|--------|-------------------------|------------------------------|---------------|
| GET    | `/evaluations`          | List evaluations             | 0, 1, 2, 3    |
| GET    | `/evaluations/{id}`     | Get evaluation by ID         | 0, 1, 2, 3    |
| POST   | `/evaluations`          | Submit evaluation (video)    | 3             |
| PUT    | `/evaluations/{id}`     | Update evaluation            | 0, 1, 3       |
| DELETE | `/evaluations/{id}`     | Soft delete evaluation       | 0, 1          |

### 6.6 Evaluation Analysis

| Method | Endpoint                        | Description                  | Roles         |
|--------|---------------------------------|------------------------------|---------------|
| GET    | `/evaluation-analysis/{eval_id}`| Get analysis for evaluation  | 0, 1, 2       |
| POST   | `/evaluation-analysis`          | Create/trigger analysis      | 0, 1          |

### 6.7 Dashboard

| Method | Endpoint          | Description                      | Roles         |
|--------|-------------------|----------------------------------|---------------|
| GET    | `/dashboard`      | Get role-based dashboard summary | 0, 1, 2, 3    |

**Dashboard returns different data based on role:**
- Role 0 (Superadmin): All companies summary
- Role 1 (Admin): Company-wide statistics
- Role 2 (Manager): Assigned campaigns summary
- Role 3 (Shopper): Personal evaluation summary

### 6.8 Surveys

| Method | Endpoint             | Description              | Roles         |
|--------|----------------------|--------------------------|---------------|
| GET    | `/surveys`           | List surveys             | 0, 1, 2       |
| GET    | `/surveys/{id}`      | Get survey by ID         | 0, 1, 2, 3    |
| POST   | `/surveys`           | Create survey            | 0, 1          |
| PUT    | `/surveys/{id}`      | Update survey            | 0, 1          |

### 6.9 Zones

| Method | Endpoint             | Description              | Roles         |
|--------|----------------------|--------------------------|---------------|
| GET    | `/zones`             | List zones               | 0, 1, 2       |
| POST   | `/zones`             | Create zone              | 0, 1          |
| PUT    | `/zones/{id}`        | Update zone              | 0, 1          |

### 6.10 Notifications

| Method | Endpoint                  | Description              | Roles         |
|--------|---------------------------|--------------------------|---------------|
| GET    | `/notifications`          | List user notifications  | All           |
| PUT    | `/notifications/{id}/read`| Mark as read             | All           |

### 6.11 Payments

| Method | Endpoint             | Description              | Roles         |
|--------|----------------------|--------------------------|---------------|
| GET    | `/payments`          | List payments            | 0, 1          |
| POST   | `/payments`          | Record payment           | 0, 1          |

### 6.12 Cloudflare

| Method | Endpoint                    | Description                  | Roles         |
|--------|-----------------------------|------------------------------|---------------|
| POST   | `/cloudflare/stream/upload` | Get upload URL for video     | 3             |
| POST   | `/cloudflare/webhook`       | Webhook for video processing | System        |

---

## 7. AUTHENTICATION & AUTHORIZATION

### 7.1 JWT Token Flow

```
1. User Login:
   POST /api/v1/auth/login
   Body: { "email": "...", "password": "..." }
   ↓
   Server validates credentials
   ↓
   Returns JWT token
   Response: { "access_token": "eyJ...", "token_type": "bearer" }

2. Subsequent Requests:
   GET /api/v1/users
   Headers: { "Authorization": "Bearer eyJ..." }
   ↓
   JWT Interceptor (frontend) adds token
   ↓
   Backend validates token (app/core/security.py)
   ↓
   Request.state.user populated with user data
   ↓
   Route executes with user context
```

### 7.2 Token Structure

```python
# JWT Payload
{
    "sub": "user_id",
    "email": "user@example.com",
    "role": 1,
    "company_id": 5,
    "exp": 1672531200  # Expiration timestamp
}
```

### 7.3 Authorization Checks

**Backend (`app/utils/deps.py`):**
```python
def get_auth_user(request: Request) -> User:
    # Validates JWT and returns current user

def check_company_payment_status(request: Request):
    # Ensures company subscription is active
```

**Frontend (`app/guards/auth.guard.ts`):**
```typescript
// Protects routes, redirects to login if not authenticated
```

### 7.4 Password Security

- **Hashing:** Bcrypt with auto-generated salt
- **Validation:** Min 8 characters, max 40
- **Storage:** Only `hashed_password` stored in database

---

## 8. AI INTEGRATION ARCHITECTURE

### 8.1 Dual-Prompt Analysis System

**Objective:** Provide both executive storytelling AND structured operational data from video transcriptions.

**Flow:**
```
1. Video Upload (Shopper)
   ↓ Cloudflare Stream stores video
   
2. Audio Extraction (Backend)
   ↓ MoviePy extracts audio from video
   
3. Transcription (OpenAI Whisper)
   ↓ POST to OpenAI Whisper API
   ↓ Returns Spanish text transcription
   
4. Dual Analysis (GPT-4o)
   ↓ Single prompt requesting 2 views:
   ↓ a) Vista Ejecutiva (narrative, insights, NPS)
   ↓ b) Vista Operativa (JSON with KPIs)
   
5. Parse Response
   ↓ Split into executive_view + operative_view
   
6. Store in evaluation_analysis table
   ↓ Full response + parsed views
```

### 8.2 AI Prompt Architecture

**Located:** `app/services/openai_services.py`

**System Prompt Components:**

1. **Role Definition:**
   - Dual analyst (consultive + methodological)
   - CX industry standards (Forrester, Bain NPS, Gartner CES)

2. **Vista Ejecutiva (Executive View):**
   - 🧾 Executive summary
   - 🧠 Key transcription snippets
   - 📌 Main topics
   - 😐 Emotional tone analysis
   - 📊 Quantitative evaluation (1-5 scale)
   - ✅ Best practices observed
   - ⚠ Improvement opportunities
   - 🚀 Training recommendations
   - 📈 Inferred NPS (0-10 scale)
   - 🧩 Business impact estimation

3. **Vista Operativa (Operative View):**
   - **JSON Schema** with deterministic KPIs:
     - **IOC** (Índice Oportunidad Comercial): 0-100
     - **IRD** (Índice Riesgo Deserción): 0-100
     - **CES** (Customer Effort Score): 0-100
     - **Calidad Básica**: Boolean checks (greeting, identification, offer, closure, value-added)
     - **Verbatims**: Exact quotes (positive, negative, critical)
     - **Acciones Sugeridas**: Automated action recommendations

### 8.3 Analysis Result Storage

**Model:** `evaluation_analysis`

```python
{
    "id": 123,
    "evaluation_id": 456,
    "analysis": "full GPT-4o response text",
    "executive_view": "Vista Ejecutiva markdown text",
    "operative_view": '{"IOC": {"score": 75, ...}, "IRD": {...}}',
    "created_at": "2025-01-15T10:30:00"
}
```

### 8.4 Future AI Enhancements (Phases 1-3)

- [ ] **PromptManager:** CRUD for company-specific prompts
- [ ] **Async AIWorker:** Background task queue for analysis
- [ ] **Insight Engine:** Aggregate trends, auto-tagging, NPS evolution
- [ ] **Training Module:** AI-suggested training plans based on patterns

---

## 9. DATA FLOW

### 9.1 Evaluation Submission Flow

```
┌─────────────┐
│  Shopper    │
│  (Angular)  │
└──────┬──────┘
       │ 1. Submit evaluation form
       │    + video file
       ▼
┌─────────────────────┐
│ Frontend Service    │
│ evaluation.service  │
└──────┬──────────────┘
       │ 2. POST /evaluations
       │    (multipart/form-data)
       ▼
┌─────────────────────────┐
│ Backend Route           │
│ evaluation_router.py    │
└──────┬──────────────────┘
       │ 3. Validate request
       │    Check auth, company status
       ▼
┌──────────────────────────┐
│ Cloudflare Stream        │
│ cloudflare_stream_service│
└──────┬───────────────────┘
       │ 4. Upload video
       │    Returns video_uid
       ▼
┌──────────────────────────┐
│ Database                 │
│ evaluations table        │
└──────┬───────────────────┘
       │ 5. Create evaluation record
       │    status = "pending"
       ▼
┌──────────────────────────┐
│ Webhook Trigger          │
│ (Cloudflare → Backend)   │
└──────┬───────────────────┘
       │ 6. Video ready
       │    status = "analyzing"
       ▼
┌──────────────────────────┐
│ Audio Extraction         │
│ extract_audio_services   │
└──────┬───────────────────┘
       │ 7. Extract audio from video
       │    Save temporary .mp3
       ▼
┌──────────────────────────┐
│ OpenAI Whisper           │
│ openai_services.py       │
└──────┬───────────────────┘
       │ 8. Transcribe audio
       │    Returns text
       ▼
┌──────────────────────────┐
│ OpenAI GPT-4o            │
│ openai_services.py       │
└──────┬───────────────────┘
       │ 9. Dual analysis
       │    Returns Vista Ejecutiva + Operativa
       ▼
┌──────────────────────────┐
│ Parse & Store            │
│ evaluation_analysis_svc  │
└──────┬───────────────────┘
       │ 10. Split response
       │     Save to evaluation_analysis
       ▼
┌──────────────────────────┐
│ Update Status            │
│ status = "completed"     │
└──────┬───────────────────┘
       │ 11. Notify shopper
       │     Create notification
       ▼
┌──────────────────────────┐
│ Frontend Notification    │
│ (Real-time or polling)   │
└──────────────────────────┘
```

### 9.2 Dashboard Data Aggregation

```
Admin Dashboard Request
   ↓
GET /api/v1/dashboard
   ↓
Check user role (request.state.user.role)
   ↓
┌─────────────┬────────────┬───────────┬──────────┐
│ Role 0      │ Role 1     │ Role 2    │ Role 3   │
│ Superadmin  │ Admin      │ Manager   │ Shopper  │
└──────┬──────┴──────┬─────┴─────┬─────┴────┬─────┘
       │             │           │          │
       ▼             ▼           ▼          ▼
get_superadmin  get_company  get_manager  get_user
   _summary      _users       _summary    _evaluation
               _evaluations              _summary
       │             │           │          │
       └─────────────┴───────────┴──────────┘
                     │
                     ▼
          Aggregate data from:
          - evaluations
          - evaluation_analysis
          - campaigns
          - users
                     │
                     ▼
          Return JSON summary
```

---

## 10. MODULE DESCRIPTIONS

### 10.1 Backend Modules

#### **app/core**
- **config.py:** Pydantic settings, loads environment variables
- **db.py:** AsyncSession factory, database connection pooling
- **security.py:** JWT creation/validation, password hashing

#### **app/models**
- SQLModel definitions (ORM + Pydantic validation)
- Each model has: Base, Create, Update, Public schemas
- Relationships defined with `Relationship(back_populates=...)`

#### **app/routes**
- FastAPI endpoint definitions
- Request validation (Pydantic models)
- Dependency injection for auth, database
- Response formatting

#### **app/services**
- Business logic layer
- Database queries (async SQLAlchemy)
- External API integrations
- Data transformations

### 10.2 Frontend Modules

#### **app/services**
- Angular services for API communication
- HttpClient usage with observables (RxJS)
- Error handling and response mapping

#### **app/guards**
- Route protection (auth.guard.ts)
- Checks JWT token validity
- Redirects to login if unauthorized

#### **app/interceptors**
- JWT interceptor adds `Authorization` header
- Global error handling
- Request/response transformations

#### **app/pages**
- Smart components (container components)
- Route-level components
- Integrate multiple services and child components

#### **app/components**
- Reusable presentational components
- Input/output properties
- UI-focused, minimal business logic

---

## 11. NAMING CONVENTIONS

### 11.1 Backend

**Files:**
- Models: `{entity}_model.py` (e.g., `user_model.py`)
- Routes: `{entity}_router.py` (e.g., `campaign_router.py`)
- Services: `{entity}_services.py` (e.g., `evaluation_services.py`)

**Classes:**
- PascalCase: `UserPublic`, `CampaignCreate`
- Suffixes: `Base`, `Create`, `Update`, `Public`

**Functions:**
- snake_case: `get_user_by_id()`, `create_evaluation()`
- Async: prefix with `async def`

**Database Tables:**
- Plural snake_case: `users`, `campaigns`, `evaluation_analysis`

### 11.2 Frontend

**Files:**
- Components: `{name}.component.ts` (e.g., `page-header.component.ts`)
- Services: `{name}.service.ts` (e.g., `auth.service.ts`)
- Interfaces: `{name}.ts` (e.g., `user.ts`, `campaign.ts`)
- Guards: `{name}.guard.ts`

**Classes:**
- PascalCase: `AuthService`, `UserComponent`

**Functions/Methods:**
- camelCase: `getUserById()`, `submitEvaluation()`

**Variables:**
- camelCase: `currentUser`, `evaluationList`

**Constants:**
- UPPER_SNAKE_CASE: `API_BASE_URL`, `TOKEN_KEY`

---

## 12. ENVIRONMENT CONFIGURATION

### 12.1 Backend Environment Variables

**File:** `cx-backend/.env`

```bash
# Project
PROJECT_NAME="Siete CX Backend"
PROJECT_URL="https://cx-api.sieteic.com"
API_URL="/api/v1"

# JWT Authentication
JWT_SECRET_KEY="your-secret-key-change-in-production"
JWT_ALGORITHM="HS256"
JWT_EXPIRE=1440  # Minutes (24 hours)

# PostgreSQL Database
POSTGRES_URI="postgresql+asyncpg://user:pass@host:5432/dbname"

# AWS S3 (Legacy/Optional)
AWS_ACCESS_KEY_ID="your-aws-key"
AWS_SECRET_ACCESS_KEY="your-aws-secret"
AWS_BUCKET_NAME="siete-cx-files"

# Cloudflare Stream (Video Hosting)
CLOUDFLARE_STREAM_KEY="your-cloudflare-stream-token"
CLOUDFLARE_ACCOUNT_ID="your-cloudflare-account-id"

# Cloudflare R2 (Object Storage)
R2_ACCESS_KEY_ID="your-r2-access-key"
R2_SECRET_ACCESS_KEY="your-r2-secret"
R2_BUCKET="siete-cx-videos"
R2_ENDPOINT_URL="https://your-account.r2.cloudflarestorage.com"

# OpenAI API
OPENAI_API_KEY="sk-..."

# SendGrid (Future)
SENDGRID_API_KEY="SG...."

# Twilio (Future)
TWILIO_ACCOUNT_SID="AC..."
TWILIO_AUTH_TOKEN="..."
```

### 12.2 Frontend Environment Variables

**File:** `cx-frontend/src/environments/environment.ts`

```typescript
export const environment = {
  production: false,
  apiUrl: 'http://localhost:8000/api/v1',
  cloudflareStreamUrl: 'https://customer-stream.cloudflarestream.com',
};
```

**File:** `cx-frontend/src/environments/environment.prod.ts`

```typescript
export const environment = {
  production: true,
  apiUrl: 'https://cx-api.sieteic.com/api/v1',
  cloudflareStreamUrl: 'https://customer-stream.cloudflarestream.com',
};
```

---

## 13. DEPLOYMENT ARCHITECTURE

### 13.1 Railway.app Deployment

```
┌──────────────────────────────────────────┐
│         Railway.app Project              │
├──────────────────────────────────────────┤
│                                          │
│  ┌────────────────────────────────┐     │
│  │  PostgreSQL 14 Service         │     │
│  │  - Auto-provisioned database   │     │
│  │  - Connection string in env    │     │
│  └────────────────────────────────┘     │
│                                          │
│  ┌────────────────────────────────┐     │
│  │  FastAPI Backend Service       │     │
│  │  - Python 3.13                 │     │
│  │  - Auto-deploy from GitHub     │     │
│  │  - Domain: cx-api.sieteic.com  │     │
│  └────────────────────────────────┘     │
│                                          │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│      External Hosting (Frontend)         │
│  - Vercel / Netlify / Railway            │
│  - Angular build artifacts (dist/)       │
│  - Domain: cx.sieteic.com                │
└──────────────────────────────────────────┘

┌──────────────────────────────────────────┐
│      Cloudflare Infrastructure           │
│  - Stream: Video hosting & transcoding   │
│  - R2: Object storage (S3-compatible)    │
└──────────────────────────────────────────┘
```

### 13.2 Deployment Workflow (Current)

**Backend:**
1. Push to GitHub repository (`cx-backend`)
2. Railway auto-detects changes
3. Builds Docker container (Python 3.13)
4. Runs Alembic migrations
5. Starts FastAPI server (uvicorn)
6. Health check validates deployment

**Frontend:**
1. Push to GitHub repository (`cx-frontend`)
2. Hosting platform (Vercel/Netlify) auto-deploys
3. Builds Angular production bundle (`ng build --prod`)
4. Serves static files via CDN

### 13.3 CI/CD Pipeline (Phase 5 - Future)

**GitHub Actions Workflow:**
```yaml
# .github/workflows/deploy.yml
name: Deploy Siete CX

on:
  push:
    branches: [main]

jobs:
  test-backend:
    - Run pytest (unit + integration tests)
    - Check code coverage (80%+ required)
  
  test-frontend:
    - Run Jasmine tests
    - Check code coverage
  
  deploy-backend:
    - Deploy to Railway
    - Run migrations
    - Health check
  
  deploy-frontend:
    - Build Angular production
    - Deploy to hosting
```

---

## 14. INTEGRATION POINTS

### 14.1 OpenAI Integration

**Services:**
- **Whisper:** Audio transcription (Spanish)
- **GPT-4o:** Dual-prompt CX analysis

**Authentication:** API Key (Bearer token)

**Endpoints:**
- `POST https://api.openai.com/v1/audio/transcriptions`
- `POST https://api.openai.com/v1/chat/completions`

**Rate Limits:** 10,000 RPM (adjust based on plan)

### 14.2 Cloudflare Stream

**Purpose:** Video hosting, transcoding, adaptive streaming

**Flow:**
1. Backend requests upload URL: `POST /stream`
2. Frontend uploads video via TUS protocol
3. Cloudflare transcodes video
4. Webhook notifies backend: `POST /cloudflare/webhook`
5. Backend triggers AI analysis

**Authentication:** API Token

### 14.3 Cloudflare R2

**Purpose:** S3-compatible object storage for files

**SDK:** Boto3 (AWS SDK for Python)

**Use Cases:**
- Store extracted audio files
- Store generated reports (PDF/Excel)
- Backup video metadata

### 14.4 SendGrid (Future - Phase 4)

**Purpose:** Transactional emails

**Use Cases:**
- Evaluation completion notifications
- Campaign assignment alerts
- Weekly summary reports

### 14.5 Twilio (Future - Phase 4)

**Purpose:** SMS notifications

**Use Cases:**
- Critical alert notifications
- Two-factor authentication (2FA)

---

## APPENDIX A: ROLES & PERMISSIONS MATRIX

| Feature                   | Superadmin (0) | Admin (1) | Manager (2) | Shopper (3) |
|---------------------------|----------------|-----------|-------------|-------------|
| View all companies        | ✅             | ❌        | ❌          | ❌          |
| Manage own company        | ✅             | ✅        | ❌          | ❌          |
| Create campaigns          | ✅             | ✅        | ❌          | ❌          |
| View assigned campaigns   | ✅             | ✅        | ✅          | ✅          |
| Submit evaluations        | ❌             | ❌        | ❌          | ✅          |
| View all evaluations      | ✅             | ✅        | ✅          | ❌          |
| View own evaluations      | ✅             | ✅        | ✅          | ✅          |
| Manage users              | ✅             | ✅        | ❌          | ❌          |
| View dashboard            | ✅             | ✅        | ✅          | ✅          |
| Access AI analysis        | ✅             | ✅        | ✅          | ❌          |
| Manage payments           | ✅             | ✅        | ❌          | ❌          |

---

## APPENDIX B: DATABASE MIGRATIONS

**Tool:** Alembic

**Commands:**
```bash
# Create new migration
alembic revision --autogenerate -m "Add new table"

# Apply migrations
alembic upgrade head

# Rollback last migration
alembic downgrade -1

# View migration history
alembic history
```

**Migration Folder:** `cx-backend/app/migrations/versions/`

---

## APPENDIX C: TESTING STRATEGY

**Backend Testing (Pytest):**
- Unit tests for services
- Integration tests for API endpoints
- Mock external APIs (OpenAI, Cloudflare)
- Target: 80%+ coverage

**Frontend Testing (Jasmine):**
- Unit tests for services
- Component tests
- E2E tests (future)
- Target: 80%+ coverage

---

## CONCLUSION

This architecture document serves as the **single source of truth** for the Siete CX platform. All development, enhancements, and integrations should reference and update this document.

**For questions or clarifications:**
- Technical Lead: [To be assigned]
- Documentation: `/app/cx-backend/docs/`

**Next Steps:**
- Phase 1: Core Functionality Refinements
- Phase 2: Dashboards Premium
- Phase 3: Intelligence CX Enhancements
- Phase 4: Omnichannel & UX
- Phase 5: CI/CD & Testing
- Phase 6: Reserve Features

---

**Last Updated:** January 2025  
**Version:** 1.0  
**Status:** ✅ Phase 0 Complete
