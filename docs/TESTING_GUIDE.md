# MWECAU Digital Voting System - Testing Guide (code-verified)

This guide shows how to test the system against the code in this repository. It focuses on practical steps and correct endpoint paths.

Local dev notes
- Run from repo root:
```bash
cd src
python manage.py runserver
```
- By default Django runs on port `8000`. The settings `SITE_URL` defaults to `http://localhost:5000`; examples below use `http://localhost:8000` unless you override the port.

Admin and sample accounts
- Admin account (if created by management commands or fixtures): `admin@mail.com` / `@12345678` (verify in `src/management/commands` or DB).

Primary test flows
1) Registration & Login (API helpers exist in `src/core/api_views.py` but are not always wired into URL patterns; UI registration/login are available under `/register/` and `/login/`).
2) Election listing (UI): `GET /elections/`
3) Vote (UI): `POST /elections/<election_id>/vote/submit/` (form)
4) Vote (API): `POST /elections/api/<election_id>/submit/` (JSON)
5) Results (API): `GET /elections/api/<election_id>/results/`

API quick examples (use correct paths)
- Get elections (UI page): `GET /elections/`
- Cast a vote (API):
```http
POST http://localhost:8000/elections/api/1/submit/
Authorization: Bearer <ACCESS_TOKEN>  # or use session cookie from login
Content-Type: application/json

{
  "token": "550e8400-e29b-41d4-a716-446655440000",
  "candidate_id": 5
}
```
- View results (API):
```http
GET http://localhost:8000/elections/api/1/results/
Authorization: Bearer <ACCESS_TOKEN>
```

Where to find tokens for testing
- In production tokens are emailed when an election is activated. In development you can:
  - Query the `voter_tokens` table directly (SQLite/DB) for `token` values.
  - Run `notify_voters_of_active_election` task manually (it is a Celery task but can be invoked directly for testing) or start Celery workers and let it run asynchronously.

Enabling Celery (optional but recommended for asynchronous emails)
```bash
cd src
# start worker
celery -A mw_es worker -Q email_queue --loglevel=info
# start beat (scheduler)
celery -A mw_es beat --loglevel=info
```
If not running workers, functions implemented as tasks may execute synchronously when called directly.

Management commands (setup)
- Common commands to prepare a dev environment (run from `src/`):
```bash
python manage.py update_states
python manage.py import_college_data
python manage.py create_admin_user
python manage.py create_student_accounts
python manage.py create_elections
python manage.py create_sample_election
```

Smoke tests
- Cast a vote with a valid token and confirm:
  - `VoterToken.is_used` is True after voting.
  - A `Vote` record exists and has `election` and `election_level` populated.
- Attempt to vote twice with the same token — second attempt should fail with validation error.

DB quick checks (SQLite)
- List tokens for a user and an election:
```sql
SELECT id, token, is_used, expiry_date FROM voter_tokens WHERE user_id = <id> AND election_id = <id>;
```
- Verify vote recorded:
```sql
SELECT * FROM votes WHERE token_id = <token_id>;
```

Notes & known limitations
- Celery is configured in settings to use the Django DB broker; however some code paths call task functions synchronously. Start Celery workers to enable asynchronous background processing.
- Some API helper endpoints implemented in `src/core/api_views.py` may not be registered under global URL confs; verify `src/mw_es/urls.py` and `src/core/urls.py` if you expect additional API routes.


#### 2. Register New Account
```http
POST /api/auth/register/
Content-Type: application/json

{
  "registration_number": "T/ADM/2020/0001",
  "email": "paul.mbise@mail.com",
  "password": "@2025",
  "password_confirm": "@2025",
  "first_name": "Paul",
  "last_name": "Mbise",
  "state": 1,
  "course": 1
}
```

### Reference Data Endpoints

#### 3. Get States
```http
GET /api/states/

Response:
[
  {"id": 1, "name": "KWACHANGE"},
  {"id": 2, "name": "KIFUMBU"},
  ...
]
```

#### 4. Get Courses
```http
GET /api/courses/

Response:
[
  {"id": 1, "code": "BsChem", "name": "Bachelor of Science in Chemistry"},
  {"id": 2, "code": "BsCS", "name": "Bachelor of Science in Computer Science"},
  ...
]
```

### Election Endpoints

#### 5. List Active Elections
```http
GET /api/election/list/
Authorization: Bearer <access_token>

Response:
[
  {
    "id": 1,
    "title": "University Elections 2025",
    "description": "...",
    "start_date": "2025-10-22...",
    "end_date": "2025-10-29...",
    "is_active": true,
    "has_ended": false,
    "levels": [
      {
        "id": 1,
        "name": "University President",
        "code": "PRES-2025",
        "type": "president",
        "description": "...",
        "course": null,
        "state": null,
        "course_details": null,
        "state_details": null
      },
      {
        "id": 2,
        "name": "KWACHANGE State Leader",
        "code": "STATE-KWACHANGE-2025",
        "type": "state",
        "description": "...",
        "course": null,
        "state": 1,
        "course_details": null,
        "state_details": {"id": 1, "name": "KWACHANGE"}
      },
      ...
    ]
  }
]
```

#### 6. Cast Vote
```http
POST /api/election/vote/
Authorization: Bearer <access_token>
Content-Type: application/json

{
  "token": "550e8400-e29b-41d4-a716-446655440000",
  "candidate_id": 1
}

Response:
{
  "message": "Vote successfully cast."
}
```

#### 7. View Results
```http
GET /api/election/results/1/
Authorization: Bearer <access_token>

Response:
[
  {
    "position_id": 1,
    "position_title": "University President",
    "total_votes_cast": 100,
    "candidates": [
      {
        "candidate_id": 1,
        "candidate_name": "Paul Mbise",
        "candidate_image_url": "http://...",
        "vote_count": 60,
        "vote_percentage": 60.0
      },
      ...
    ]
  }
]
```

## 🧪 Testing the Three-Level Election System

### Test Scenario 1: President Level (All Voters Eligible)

**Objective**: Verify all verified voters receive tokens for the President level

**Steps**:
1. Login as any student (e.g , `reg-001@mail.com` / `@2025`)
2. Call `GET /api/election/list/` to see active elections
3. Verify the response includes the President level
4. **To get your voting token**: Tokens are generated when elections are activated via email
5. For testing, check the database:
   ```sql
   SELECT token FROM voter_tokens 
   WHERE user_id = <your_user_id> 
   AND election_id = 1 
   AND election_level_id = 1;
   ```

### Test Scenario 2: State Level (Filtered by State)

**Objective**: Verify only voters from a specific state get tokens for that state's level

**Steps**:
1. Check which state a user is assigned to:
   ```sql
   SELECT state_id FROM users WHERE registration_number = 'T/ADM/2020/0001';
   ```
2. Login as that user
3. Check election levels - you should only see state levels matching your state
4. Attempt to vote for a candidate in a different state's level (should fail)

### Test Scenario 3: Course Level (Filtered by Course)

**Objective**: Verify only voters from a specific course get tokens for that course's level

**Steps**:
1. Check which course a user is assigned to:
   ```sql
   SELECT course_id FROM users WHERE registration_number = 'T/ADM/2020/0001';
   ```
2. Login as that user
3. Check election levels - you should only see course levels matching your course
4. Attempt to vote for a candidate in a different course's level (should fail)

## Testing Token Security (Partial Blockchain)

### Test 1: Token Uniqueness
```sql
-- Verify each user has exactly one token per election per level
SELECT user_id, election_id, election_level_id, COUNT(*) as token_count
FROM voter_tokens
GROUP BY user_id, election_id, election_level_id
HAVING COUNT(*) > 1;
-- Should return no results
```

### Test 2: Token Immutability
1. Cast a vote using a token
2. Attempt to vote again with the same token
3. Expected result: Error "Token is either used or expired"

### Test 3: Token Validation
```http
POST /api/election/vote/
{
  "token": "invalid-uuid",
  "candidate_id": 1
}
-- Should return: "Invalid token UUID provided"
```

## Complete Voting Flow Test

### 1. Student Registration
```http
POST /api/auth/register/
{
  "registration_number": "T/ADM/2020/0001",
  "email": "test@mail.com",
  "password": "@2025",
  "password_confirm": "@2025",
  "first_name": "Test",
  "last_name": "User",
  "state": 1,
  "course": 1
}
```

### 2. Login
```http
POST /api/auth/login/
{
  "registration_number": "T/ADM/2020/0001",
  "password": "@2025"
}
-- Save the access_token from response
```

### 3. View Elections
```http
GET /api/election/list/
Authorization: Bearer <access_token>
```

### 4. Get Voting Token
**Note**: Tokens are normally sent via email when an election is activated. For testing, query the database:
```sql
SELECT token, election_level_id 
FROM voter_tokens 
WHERE user_id = <your_id> AND election_id = 1;
```

### 5. Cast Vote
```http
POST /api/election/vote/
Authorization: Bearer <access_token>
{
  "token": "<your_token_uuid>",
  "candidate_id": <candidate_id>
}
```

### 6. Verify Vote Recorded
```sql
SELECT * FROM votes WHERE token_id = <token_id>;
-- Check that election, election_level, and voter are auto-populated
```

### 7. Check Results (as commissioner or after election ends)
```http
GET /api/election/results/1/
Authorization: Bearer <access_token>
```

## 🛠️ Django Admin Panel

Access the admin panel at: `http://localhost:5000/admin/`

**Login**: `admin@mail.com` / `@12345678`

**Available Admin Sections**:
- Users (view/edit all user accounts)
- States & Courses
- College Data
- Elections & Election Levels
- Positions & Candidates
- Voter Tokens (view token status)
- Votes (view anonymized vote records)

## Management Commands

### Run all setup commands at once:
```bash
python manage.py update_states
python manage.py import_college_data
python manage.py create_admin_user
python manage.py create_student_accounts
python manage.py create_elections
python manage.py create_sample_election
```

### Individual commands:
```bash
# Create states
python manage.py update_states

# Import college data from CSV
python manage.py import_college_data

# Create admin and commissioner users
python manage.py create_admin_user

# Create student accounts from college data
python manage.py create_student_accounts

# Create election levels and positions
python manage.py create_elections

# Create sample active election
python manage.py create_sample_election
```

## Known Limitations

1. **Celery Not Configured**: Email notifications run synchronously (not in background)
2. **Token Distribution**: Currently, tokens must be retrieved from database. In production, they would be sent via email when elections are activated.
3. **No Candidate Data Yet**: You'll need to create candidates via Django admin panel or API
4. **Database**: Using SQLite for development. Migrate to PostgreSQL for production.

## Documentation References

- **Business Logic**: See `ELECTION_BUSINESS_LOGIC.md` for detailed explanation of the three-level system and token architecture
- **System Architecture**: See `README..md` for overall system design and rationale
