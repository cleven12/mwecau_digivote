# MWECAU Digital Voting System - API Documentation

## Base URL
```
Production: https://your-repl-name.repl.co
Development: http://localhost:5000
```

## Authentication
Most endpoints require JWT (JSON Web Token) authentication. Include the token in the Authorization header:
```
Authorization: Bearer <your_access_token>
```

---

## 1. AUTHENTICATION ENDPOINTS

### 1.1 Login
**Endpoint:** `POST /api/auth/login/`  
**Authentication:** Not required  
**Description:** Authenticate user and receive JWT tokens

**Request Body:**
```json
{
  # API Documentation (code-verified)

  This document lists the API endpoints that are implemented and reachable from the codebase as of 2025-12-07. The source of truth is the Python code under `src/`.

  Base URL
  - Local development: `http://localhost:8000` (Django `runserver` default) or set `SITE_URL`/runserver port as desired. The project `SITE_URL` default (`src/mw_es/settings.py`) is `http://localhost:5000` — adjust examples to your environment.

  Authentication
  - API views accept either JWT Bearer tokens (`djangorestframework-simplejwt`) or Django sessions (see `REST_FRAMEWORK.DEFAULT_AUTHENTICATION_CLASSES` in `src/mw_es/settings.py`).
  - Include JWT tokens in the `Authorization` header: `Authorization: Bearer <ACCESS_TOKEN>`.

  Where to look in code
  - Election API views: `src/election/views.py` (`VoteView`, `ResultsView`).
  - Commissioner APIs: `src/core/views_commissioner.py` (endpoints under `core.urls`).
  - Some auth-related API helpers and viewsets live in `src/core/api_views.py` but are not registered under top-level URL patterns in this repository — check the file for available handlers.

  Important URL patterns (as implemented)
  - UI & commissioner APIs (registered in `src/core/urls.py`):
    - `GET /` — home (UI)
    - `GET /login/`, `POST /login/` — session-based login (UI)
    - `GET /dashboard/` — user dashboard (UI)
    - `GET /commissioner/` — commissioner dashboard (UI)
    - `GET /api/commissioner/stats/` — commissioner stats (JSON)
    - `GET /api/commissioner/election/<election_id>/analytics/` — election analytics (JSON)
    - `POST /api/commissioner/verify-user/<user_id>/` — verify user (commissioner only)
    - `GET /api/commissioner/pending-verifications/` — pending users list

  - Election UI and minimal API (registered in `src/election/urls.py`):
    - `GET /elections/` — elections list (UI)
    - `GET /elections/<election_id>/vote/` — vote page (UI)
    - `POST /elections/<election_id>/vote/submit/` — UI vote submit (form)
    - `GET /elections/<election_id>/results/` — results page (UI)
    - `POST /elections/api/<election_id>/submit/` — API vote submission (JSON)
    - `GET  /elections/api/<election_id>/results/` — API results (JSON)

  Vote submission (API)
  - Endpoint: `POST /elections/api/<election_id>/submit/`
  - Auth: JWT or session (user must be authenticated)
  - Payload (JSON):
    - `token` (UUID string) — the voter token UUID
    - `candidate_id` (integer) — candidate primary key
  - Example:
  ```json
  POST /elections/api/1/submit/
  {
    "token": "550e8400-e29b-41d4-a716-446655440000",
    "candidate_id": 5
  }
  ```
  - Behavior: the request is validated by `VoteCreateSerializer` (`src/election/serializers.py`). On success a `Vote` is created, the token is marked used, and a confirmation email helper (`send_vote_confirmation_email`) is called (note: the helper is a Celery task but may be called synchronously in code paths).

  Results (API)
  - Endpoint: `GET /elections/api/<election_id>/results/`
  - Auth: JWT or session. Results are available to commissioners/staff any time; regular users can access after the election's `has_ended` flag is True.
  - Response: JSON list of positions with candidate vote counts and percentages.

  Commissioner endpoints (examples)
  - `GET /api/commissioner/stats/` — overall stats (requires commissioner role)
  - `GET /api/commissioner/election/<id>/analytics/` — per-election analytics
  - `POST /api/commissioner/verify-user/<user_id>/` — verify a user (commissioner only)

  Notes and caveats
  - Some API helper views and viewsets are implemented in `src/core/api_views.py` (login/register endpoints, state/course viewsets, user viewset) but are not registered to a URL router in `src/mw_es/urls.py` or `src/core/urls.py` by default in this branch — check the repository to expose them if needed.
  - Celery is configured in settings and tasks are defined, but several places in the code call task functions synchronously instead of using `.delay()`; to run tasks asynchronously start a Celery worker and `celery beat` as documented in `docs/ARCHITECTURE.md` and `docs/CONTRIBUTING.md`.

  If you need a machine-readable OpenAPI/Swagger spec, the project does not currently register `drf-yasg` or `drf-spectacular` routes; consider adding a schema generator and registering `/swagger/` if required.

  For more details about business rules and token lifecycle see `docs/ELECTION_BUSINESS_LOGIC.md`.
