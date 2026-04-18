# 📊 Land & Property Management API

![Land & Property Management Dashboard](/home/cttxl/.gemini/antigravity/brain/778d9873-1cf8-43c0-a94e-6d0612527b96/land_property_management_hero_1776554469235.png)

A comprehensive RESTful API system designed for **United Territorial Communities (UTCs)** to synchronize, audit, and manage land and property assets with precision.

---

## 📖 Project Overview

In many municipal environments, a systemic discrepancy exists between the physical state of assets and official records. This leads to revenue loss and inefficient resource management. 

Our solution provides:
- **🔄 Data Synchronization**: Real-time alignment between disparate registry systems.
- **⚖️ Audit & Control**: Robust capabilities to track and verify asset utilization.
- **📈 Revenue Recovery**: Automated identification of misclassified properties for taxation.
- **🤝 Transparency**: Consolidated records to foster public trust and accountability.

### 🛠 Tech Stack
*   **Backend**: Python, Django, DRF, SQLite/PostgreSQL
*   **Frontend**: React, Next.js, Vite
*   **DevOps**: Docker, Docker Compose, Makefile

---

## 🚀 Getting Started

### Prerequisites
*   [Docker](https://www.docker.com/get-started) & [Docker Compose](https://docs.docker.com/compose/install/)
*   `make` (GNU Make)

### Quick Launch
Deploy the entire stack (Frontend & Backend) in seconds:

```bash
make up
```

| Service | Access URL |
| :--- | :--- |
| **Frontend Application** | [http://localhost:3000](http://localhost:3000) |
| **Backend API** | [http://localhost:8000](http://localhost:8000) |

### 🎮 Makefile Reference
| Command | Description |
| :--- | :--- |
| `make up` | Builds and starts all services in background. |
| `make down` | Stops and removes all containers/networks. |
| `make backend-up` | Builds and starts only the Backend API. |
| `make frontend-up` | Builds and starts only the Frontend App. |
| `make backend-logs` | Follow real-time logs for the backend. |

---

## 🔒 Security & Standards

### 🔑 Authentication
All endpoints (excluding `/api/auth/*`) require a valid **JWT Access Token**. 
Include it in your HTTP headers:
```http
Authorization: Bearer <your_access_token>
```

### ⚠️ Error Protocols
Standardized JSON error responses are returned for non-2xx statuses:

| Status Code | Label | Typical Context |
| :--- | :--- | :--- |
| `400` | **Bad Request** | Missing fields, invalid file types, or malformed JSON. |
| `401` | **Unauthorized** | Missing or expired JWT access token. |
| `403` | **Forbidden** | Resource ownership mismatch (Ownership check failed). |
| `404` | **Not Found** | Specified Report or Record ID does not exist. |
| `500` | **Server Error** | Internal system fault or unexpected crash. |

---

## 🔐 Authentication API

### 1. Register User
`POST /api/auth/register/`  
Create a new system user.

**Request Body:**
```json
{
  "email": "admin@utc.gov.ua",
  "password": "secure_password",
  "name": "Admin User"
}
```

### 2. Login User
`POST /api/auth/login/`  
Authenticate and retrieve an access token.

**Success Response (200 OK):**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "Bearer"
}
```

---

## 📊 Report Management

### 3. Create Report (FileUpload)
`POST /api/reports/`  
Uploads land and property `.xlsx` files for synchronization analysis.

*   **Security**: `Bearer Token`
*   **Content-Type**: `multipart/form-data`
*   **Payload**:
    *   `land` (file): Required. Excel land record.
    *   `property` (file): Required. Excel property record.

**Response:**
```json
{
  "report_id": "550e8400-e29b-41d4-a716-446655440000"
}
```

---

## 📝 Record Analysis

### Data Validation Problems
When files are merged, discrepancies are flagged using the following enums:

| Problem ID | Description |
| :--- | :--- |
| `edrpou_of_land_user` | Mismatch or missing EDRPOU code. |
| `land_user` | Discrepancy in Operator/Owner name. |
| `location` | Conflicting address or coordinate data. |
| `area` | Variance in reported land/property area. |
| `purpose` | Mismatch in land use classification. |
| `share_of_ownership` | Conflicting ownership percentage records. |

### 4. List Report Records
`GET /api/reports/{report_id}/records/`  
Paginated retrieval of records with advanced filtering.

**Query Parameters:**
- `problem` (string): Filter by enum (e.g. `?problem=area`).
- `has_problems` (bool): `true` for flagged, `false` for valid.
- `location` (string): Fuzzy search by area name.
- `sort_by`: Field name or `count_of_problems`.
- `order`: `asc` or `desc`.

---

## 📄 AI & Export Functions

### 5. Bulk Export Reports
`POST /api/reports/export/`  
Generates a combined PDF report for multiple sync sessions.

**Request Body:**
```json
{
  "report_ids": ["uuid-1", "uuid-2"]
}
```

### 6. AI Discrepancy Analysis
`POST /api/reports/ai-analysis/`  
Natural language processing for answering complex questions about asset data.

**Request Body:**
```json
{
  "report_id": "uuid-sync-unit",
  "question": "Which records show the highest risk of revenue loss?"
}
```

---

> [!TIP]
> To export specific **records** from a single report, use:
> `POST /api/reports/{report_id}/export/` with `{"record_ids": ["id1", "id2"]}`.
