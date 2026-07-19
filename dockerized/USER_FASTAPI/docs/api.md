# FastAPI DB Restore Tool — API Reference

**Version:** 2.0.0
**Base URL:** `https://<host>:50443`
**Interactive docs:** `https://<host>:50443/api/docs` (Swagger UI)
**OpenAPI spec:** `https://<host>:50443/api/openapi.json`

---

## Authentication

This API uses **OAuth 2.0 Password Flow** with **JWT Bearer tokens**.

### Obtain a token

```http
POST /auth/token
Content-Type: application/x-www-form-urlencoded

username=user@example.com&password=secret
```

**Response `200 OK`**
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "refresh_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Use the token

```http
GET /auth/me
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Web UI:** Token is stored automatically in an **HttpOnly cookie** after
browser login — no manual header needed for page navigation.

---

## Endpoints

---

### `GET /`
Home page (HTML).
Returns the landing page. Shows action buttons if authenticated.

| | |
|---|---|
| Auth required | No |
| Response | HTML `200` |

---

### `GET /login`
Render the login form (HTML).

| | |
|---|---|
| Auth required | No |
| Query params | `signup=success` (show success banner), `next=<path>` (post-login redirect) |
| Response | HTML `200` |

---

### `POST /login`
Submit login credentials and receive JWT cookie.

| | |
|---|---|
| Auth required | No |
| Content-Type | `application/x-www-form-urlencoded` |
| Response | `302 Redirect` → `/restore` (or `next` param) on success; `401` on failure |

**Form fields**

| Field | Type | Required | Description |
|---|---|---|---|
| `email` | string | ✅ | User email address |
| `password` | string | ✅ | User password |
| `remember` | string | ❌ | Any value = 7-day token (default 30 min) |
| `next` | string | ❌ | Redirect path after login |

**cURL example**
```bash
curl -c cookies.txt -X POST https://host:50443/login \
  -d "email=user@example.com&password=secret&remember=1"
```

---

### `GET /signup`
Render the registration form (HTML).

---

### `POST /signup`
Register a new user account.

| | |
|---|---|
| Auth required | No |
| Content-Type | `application/x-www-form-urlencoded` |
| Response | `302 Redirect` → `/login?signup=success` or `400` if email taken |

**Form fields**

| Field | Type | Required |
|---|---|---|
| `email` | string | ✅ |
| `name` | string | ✅ |
| `password` | string | ✅ (min 8 chars) |

---

### `GET /logout`
Clear JWT cookies and redirect to `/login`.

---

### `POST /auth/token` ⭐ OAuth2

Standard OAuth2 password-flow token endpoint. Used by Swagger UI and API clients.

| | |
|---|---|
| Auth required | No |
| Content-Type | `application/x-www-form-urlencoded` |
| Response | `200` JSON token pair or `401` |

**Request fields** (OAuth2 standard)

| Field | Description |
|---|---|
| `username` | User email address |
| `password` | User password |
| `grant_type` | Must be `password` |

**Response `200 OK`**
```json
{
  "access_token": "<jwt>",
  "refresh_token": "<jwt>",
  "token_type": "bearer"
}
```

**Token lifetime**
- `access_token`: 30 minutes
- `refresh_token`: 7 days

**cURL example**
```bash
TOKEN=$(curl -s -X POST https://host:50443/auth/token \
  -d "username=user@example.com&password=secret&grant_type=password" \
  | jq -r .access_token)
```

---

### `POST /auth/refresh`

Exchange a valid refresh token (from cookie) for a new access token.

| | |
|---|---|
| Auth required | Refresh token cookie |
| Response | `200` `{"access_token": "..."}` or `401` |

---

### `GET /auth/me`

Return the profile of the currently authenticated user.

| | |
|---|---|
| Auth required | ✅ Bearer token |
| Response | `200` JSON user object |

**Response `200 OK`**
```json
{
  "id": 1,
  "email": "user@example.com",
  "name": "Jane Smith"
}
```

**cURL example**
```bash
curl -H "Authorization: Bearer $TOKEN" https://host:50443/auth/me
```

---

### `POST /auth/register`

Register a new user via API (JSON, not form).

| | |
|---|---|
| Auth required | No |
| Content-Type | `application/json` |
| Response | `201` JSON user or `400` if email taken |

**Request body**
```json
{
  "email": "newuser@example.com",
  "name": "John Doe",
  "password": "strongpassword123"
}
```

**Response `201 Created`**
```json
{
  "id": 42,
  "email": "newuser@example.com",
  "name": "John Doe"
}
```

---

### `GET /restore`
Render the DB Restore form (HTML).

| | |
|---|---|
| Auth required | ✅ (redirects to `/login` if not authenticated) |
| Response | HTML `200` |

---

### `POST /restore`
Submit a database restore request (creates RDS instance from snapshot).

| | |
|---|---|
| Auth required | ✅ |
| Content-Type | `application/x-www-form-urlencoded` |
| Response | `202 Accepted` plain-text status or `500` on AWS error |

**Form fields**

| Field | Description | Example |
|---|---|---|
| `snapshotname` | RDS snapshot identifier | `my-db-snapshot-20240101` |
| `endpoint` | Original DB or cluster endpoint | `mydb.cluster-abc.us-east-1.rds.amazonaws.com` |

**Response `202 Accepted`**
```
Database: my-db-snapshot-20240101 is being restored.
New Endpoint: my-db-snapshot-20240101.cluster-abc.us-east-1.rds.amazonaws.com.
DB Restore status: creating
```

**Side effects:** Logs audit row to `userinfo` table; sends Slack + email notification.

**cURL example (API client)**
```bash
curl -b cookies.txt -X POST https://host:50443/restore \
  -d "snapshotname=my-snap&endpoint=mydb.cluster-abc.us-east-1.rds.amazonaws.com"
```

---

### `GET /status`
Render the DB Status check form (HTML).

| | |
|---|---|
| Auth required | ✅ |
| Response | HTML `200` |

---

### `POST /status`
Check the restore/operational status of an RDS instance or cluster.

| | |
|---|---|
| Auth required | ✅ |
| Content-Type | `application/x-www-form-urlencoded` |
| Response | `202 Accepted` plain-text status |

**Form fields**

| Field | Description |
|---|---|
| `snapshotname` | Restored DB identifier (new name) |
| `endpoint` | Original DB endpoint (used to detect cluster vs instance) |

**Response `202 Accepted`**
```
Database: my-db-snapshot-20240101 status: available
```

---

### `GET /attachdb`
Render the Attach DB Instance form (HTML).

| | |
|---|---|
| Auth required | ✅ |

---

### `POST /attachdb`
Attach a new DB instance to an existing Aurora cluster.

| | |
|---|---|
| Auth required | ✅ |
| Content-Type | `application/x-www-form-urlencoded` |
| Response | `202 Accepted` or `400` if endpoint is not a cluster |

**Form fields**

| Field | Description | Example |
|---|---|---|
| `endpoint` | Cluster endpoint (must contain "cluster") | `mydb.cluster-abc.us-east-1.rds.amazonaws.com` |
| `instanceclass` | RDS instance class | `db.t3.small` |

**Supported instance classes**

| Family | Sizes |
|---|---|
| T3 | micro, small, medium, xlarge, 2xlarge |
| T2 | micro, small, medium, large, 2xlarge |
| M5 | large, xlarge, 2xlarge, 4xlarge |
| R5 | large, xlarge, 2xlarge, 4xlarge, 8xlarge |

---

## Error Responses

| Status | Meaning |
|---|---|
| `400` | Bad request (validation error, duplicate email, non-cluster endpoint) |
| `401` | Unauthenticated — invalid or missing JWT |
| `422` | Unprocessable entity — request body schema mismatch |
| `429` | Too many requests — rate limit exceeded (10 req/min on auth endpoints) |
| `500` | AWS API error during RDS operation |

**Error body (JSON)**
```json
{
  "detail": "Human-readable error message"
}
```

---

## Security

| Control | Implementation |
|---|---|
| Authentication | JWT OAuth 2.0 (python-jose / HS256) |
| Password hashing | bcrypt (passlib); legacy werkzeug pbkdf2 supported |
| Transport security | TLS 1.2+ enforced (Uvicorn + cert/key) |
| Token storage (web) | HttpOnly + SameSite=Lax cookie |
| Rate limiting | 10 req/min on auth paths, 200 req/min general (per IP) |
| Security headers | CSP, HSTS, X-Frame-Options, X-Content-Type-Options |
| Injection prevention | Pydantic validation + SQLAlchemy ORM (no raw SQL) |
| SSRF prevention | RDS endpoint validated against AWS hostname pattern |
| Audit logging | Every request logged (IP, user-agent, path, status, duration) |
| OWASP scans | Bandit (SAST) + Semgrep + pip-audit (SCA) + OWASP ZAP (DAST) |

---

## Environment Variables

| Variable | Description | Default |
|---|---|---|
| `shost` | PostgreSQL host | `localhost` |
| `sport` | PostgreSQL port | `5432` |
| `suser` | PostgreSQL user | `skondla` |
| `spassword` | PostgreSQL password | — |
| `sdatabase` | PostgreSQL database name | `flaskapp` |
| `SECRET_KEY` | JWT signing key (change in prod!) | hardcoded fallback |
| `SLACK_WEBHOOK_URL` | Slack incoming webhook | — |
