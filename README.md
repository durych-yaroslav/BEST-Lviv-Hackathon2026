# API Documentation

This documentation describes the RESTful API for the land and property report management system. All endpoints follow standard REST architectural patterns.

---

## 🚀 Running the Project

The application runs seamlessly via Docker Compose. Use the provided `Makefile` to orchestrate the environment.

### Makefile Commands:
- `make up`: Builds and starts all services (Frontend & Backend) in the background.
- `make down`: Stops and removes all running containers.
- `make frontend-up` / `make backend-up`: Builds and starts a specific service.
- `make frontend-down` / `make backend-down`: Stops a specific service without destroying it.

### Exposed Environment Ports:
- **Frontend App:** [http://localhost:3000](http://localhost:3000)
- **Backend API:** [http://localhost:8000](http://localhost:8000)

---

## 🔒 Global Security & Error Handling

**Authentication:** 
All endpoints (except `/api/auth/*`) require a valid JWT access token passed in the HTTP Authorization header:
`Authorization: Bearer <your_access_token>`

**Standard Error Responses:**
- `400 Bad Request`: Invalid request parameters, missing fields, or malformed JSON data.
- `401 Unauthorized`: Missing or invalid JWT access token.
- `403 Forbidden`: User does not have access to the requested resource (e.g., trying to access another user's report).
- `404 Not Found`: The requested resource (report or record) does not exist.
- `500 Internal Server Error`: An unexpected error occurred while processing the request on the server.

---

## 🔐 Authentication

### 1. Register User
**Endpoint:** `POST /api/auth/register`  
**Description:** Register a new user in the system.

**Request Body (JSON):**
```json
{
  "email": "user@example.com",
  "password": "secure_password",
  "name": "User Name"
}
```
**Success Response (201 Created):**
Returns the created user object data.

### 2. Login User
**Endpoint:** `POST /api/auth/login`  
**Description:** Authenticate a user and receive an access token.

**Request Body (JSON):**
```json
{
  "email": "user@example.com",
  "password": "secure_password"
}
```
**Success Response (200 OK):**
```json
{
  "access_token": "your_jwt_token_here",
  "token_type": "Bearer"
}
```

---

## 📊 Reports

### 3. Create Report (Upload)
**Endpoint:** `POST /api/reports`  
**Description:** Uploads two `.xlsx` files ("land" and "property"), processes them, generates a comprehensive report, and returns the unique report identifier.

**Security:** Requires Bearer Token  
**Content-Type:** `multipart/form-data`  
**Form-Data Parameters:**
- `land` (file): Required. The `.xlsx` file containing land data.
- `property` (file): Required. The `.xlsx` file containing property data.

**Success Response (201 Created):**
```json
{
  "report_id": "uuid-string-here"
}
```

---

## 📝 Report Records

### Data Validation Problems (Enum)
Records may have discrepancies or missing data when merged from "land" and "property" sources. The `problems` array in a record will contain enum strings representing these issues.

**Available Problem Types:**
- `edrpou_of_land_user`: EDRPOU code mismatch or missing data.
- `land_user`: Operator/owner name mismatch between documents.
- `location`: Conflicting location data between the sources.
- `area`: Significant deviation in defined land area.
- `date_of_state_registration_of_ownership`: Registration dates do not match.
- `share_of_ownership`: Conflicting ownership shares.
- `purpose`: Purpose of the land mismatch.

### 4. Get Report Records
**Endpoint:** `GET /api/reports/{report_id}/records`  
**Description:** Retrieves a paginated list of all records associated with a specific `report_id`. Supports dynamic filtering and sorting.

**Security:** Requires Bearer Token  
**Query Parameters (All Optional):**
- `problem` (string): Filter records that contain a specific problem enum (e.g., `?problem=area`).
- `has_problems` (boolean): Pass `true` to return only records with at least one problem, or `false` for fully valid records.
- `location` (string): Filter by exact or partial match of location.
- `cadastral_number` (string)
- `tax_number_of_pp` (string)
- `koatuu` (string)
- `sort_by` (string): Field name to sort by (e.g., `area`, `date_of_state_registration_of_ownership`) or `count_of_problems`.
- `order` (string): Sorting order, either `asc` or `desc` (default: `asc`).
- `page` (integer): Page number for pagination (default: 1).
- `size` (integer): Number of items per page (default: 50).

**Success Response (200 OK):**
```json
{
  "items": [
    {
      "report_id": "uuid-string-here",
      "record_id": "uuid-string-here",
      "problems": ["area", "location"],
      "land_data": { /* ... */ },
      "property_data": { /* ... */ }
    }
  ],
  "total": 100,
  "page": 1,
  "size": 50
}
```

### 5. Get Record Details
**Endpoint:** `GET /api/reports/{report_id}/records/{record_id}`  
**Description:** Retrieves detailed information for a specific record inside a given report. 

**Security:** Requires Bearer Token  
**Success Response (200 OK):**
```json
{
  "report_id": "uuid-string-here",
  "record_id": "uuid-string-here",
  "problems": [
    "area"
  ], 
  "land_data": {
    "cadastral_number": "string",
    "koatuu": "string",
    "form_of_ownership": "string",
    "purpose": "string",
    "location": "string",
    "type_of_agricultural_land": "string",
    "area": 0.0,
    "average_monetary_valuation": 0.0,
    "edrpou_of_land_user": "string",
    "land_user": "string",
    "share_of_ownership": 0.0,
    "date_of_state_registration_of_ownership": "2026-04-18T10:00:00Z",
    "record_number_of_ownership": "string",
    "authority_that_performed_state_registration_of_ownership": "string",
    "type": "string",
    "subtype": "string"
  },
  "property_data": {
    "tax_number_of_pp": "string",
    "name_of_the_taxpayer": "string",
    "type_of_object": "string",
    "address_of_the_object": "string",
    "date_of_state_registration_of_ownership": "2026-04-18T10:00:00Z",
    "date_of_state_registration_of_pledge_of_ownership": "2026-04-18T10:00:00Z",
    "total_area": 0.0,
    "type_of_joint_ownership": "string",
    "share_of_ownership": 0.0
  }
}
```

---

## 📄 Export

### 6. Bulk Export Reports as PDF
**Endpoint:** `POST /api/reports/export`  
**Description:** Accepts an array of report identifiers and generates a combined PDF containing the requested reports.

**Security:** Requires Bearer Token  
**Request Body (JSON):**
```json
{
  "report_ids": [
    "uuid-1",
    "uuid-2"
  ]
}```

### 7. AI Analysis
**Endpoint:** `POST /api/reports/ai-analysis`  
**Description:** Uses an AI model to analyze the discrepancies identified in a specific report. Can answer specific natural language questions about the report's data and trends.

**Security:** Requires Bearer Token  
**Request Body (JSON):**
```json
{
  "report_id": "uuid-string-here",
  "question": "What are the main risks found in this report?"
}
```

**Success Response (200 OK):**
```json
{
  "report_id": "uuid-string-here",
  "analysis": "Analysis text generated by the AI model...",
  "status": "success"
}
```

---

> **Note to developer:** If the original intent behind the old `GET /report_id/export/` endpoint was to bulk export multiple precise **records** from a single report rather than multiple whole reports themselves, you should use `POST /api/reports/{report_id}/export` with a payload of `{"record_ids": ["uuid-1", "uuid-2"]}` instead.

**Response Content-Type:** `application/pdf` (Binary file content)