# MWECAU Election Platform API Testing Guide

## Setup Instructions

1. **Ensure Dependencies**:
   - Install requirements: `pip install requests pytest django pytest-django`.
   - Ensure Django server is running: `python manage.py runserver`.
   - Start Redis: `redis-server`.
   - Start Celery: `celery -A your_project worker --loglevel=info`.

2. **Prepare Database**:
   - Apply migrations: `python manage.py makemigrations; python manage.py migrate`.
   - Seed data:
     - Create `State` (e.g., `name="Kilimanjaro"`).
     - Create `Course` (e.g., `name="Computer Science", code="CS100"`).
     - Create `User` (e.g., `registration_number="T/DEG/2020/0003", email="neema@mail.com", course=CS100, state=Kilimanjaro, is_verified=True`).
     - Create admin user (`is_staff=True, is_superuser=True`).
     - Create `ElectionLevel` (e.g., `code="president"`, `code="course"`, `code="state"`).
     - Create `Position` for each level (e.g., President, Course Leader for CS100, State Leader for Kilimanjaro).
     - Create `Candidate` (e.g., `user=T/DEG/2020/0003, position=President` with an `image`).

3. **Configure Settings**:
   - Ensure `MEDIA_URL` and `MEDIA_ROOT` are set for candidate images:
     ```python
     MEDIA_URL = '/media/'
     MEDIA_ROOT = BASE_DIR / 'media'
     ```
   - Add to `urls.py`:
     ```python
     from django.conf import settings
     from django.conf.urls.static import static
     urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
     ```
   - Verify `INSTALLED_APPS` includes `election` and `core`.

4. **JWT Token Setup**:
   - Obtain JWT for a regular user: `POST /api/auth/login/` with `registration_number` and `password`.
   - Obtain JWT for an admin user.
   - Use `Authorization: Bearer <token>` in headers for authenticated requests.

## Test Script (tests/test_election_api.py)

Below is a Python test script using `requests` and `unittest` to test all election app endpoints.

```python
import unittest
import requests
from datetime import datetime, timedelta
import uuid

BASE_URL = "http://localhost:8000/api/election/"

class ElectionAPITestCase(unittest.TestCase):
    def setUp(self):
        self.user_token = "your_user_jwt_token"  # Replace with JWT from /api/auth/login/
        self.admin_token = "your_admin_jwt_token"  # Replace with admin JWT
        self.headers_user = {"Authorization": f"Bearer {self.user_token}"}
        self.headers_admin = {"Authorization": f"Bearer {self.admin_token}"}
        self.election_id = None
        self.voter_token = str(uuid.uuid4())  # Replace with actual token from DB

    def test_create_election(self):
        """Test POST /api/election/create/ (admin-only)."""
        data = {
            "title": "2025 General Election",
            "description": "Annual student election",
            "start_date": (datetime.now() + timedelta(days=1)).isoformat(),
            "end_date": (datetime.now() + timedelta(days=2)).isoformat(),
            "levels": [1, 2, 3]  # IDs for president, course, state levels
        }
        response = requests.post(f"{BASE_URL}create/", json=data, headers=self.headers_admin)
        self.assertEqual(response.status_code, 201)
        self.election_id = response.json().get("id")
        self.assertTrue(self.election_id)

    def test_list_elections(self):
        """Test GET /api/election/list/ (authenticated users)."""
        response = requests.get(f"{BASE_URL}list/", headers=self.headers_user)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_vote(self):
        """Test POST /api/election/vote/ (authenticated users)."""
        data = {
            "election_id": self.election_id or 1,  # Use created election ID
            "election_level": 1,  # President level ID
            "candidate_id": 1,  # Candidate ID from seed data
            "token": self.voter_token
        }
        response = requests.post(f"{BASE_URL}vote/", json=data, headers=self.headers_user)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json().get("message"), "Vote cast")

    def test_results(self):
        """Test GET /api/election/results/<election_id>/ (admin-only)."""
        response = requests.get(f"{BASE_URL}results/{self.election_id or 1}/", headers=self.headers_admin)
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.json(), list)

    def test_unauthorized_access(self):
        """Test unauthorized access to admin endpoints."""
        response = requests.post(f"{BASE_URL}create/", json={}, headers=self.headers_user)
        self.assertEqual(response.status_code, 403)

if __name__ == "__main__":
    unittest.main()
```

## Testing Guide

### Running Tests
1. Save the test script as `tests/test_election_api.py`.
2. Replace `your_user_jwt_token` and `your_admin_jwt_token` with actual JWTs from `/api/auth/login/`.
3. Replace `voter_token` with a valid token from the `VoterToken` table (generated during election creation).
4. Run tests: `python -m unittest tests/test_election_api.py`.

### Manual Testing Guide
Use tools like Postman or curl to test endpoints manually.

1. **Create Election (POST /api/election/create/)**
   - **Headers**: `Authorization: Bearer <admin_jwt>`
   - **Body**:
     ```json
     {
       "title": "2025 General Election",
       "description": "Annual student election",
       "start_date": "2025-09-06T00:00:00Z",
       "end_date": "2025-09-07T23:59:59Z",
       "levels": [1, 2, 3]
     }
     ```
   - **Expected**: 201, `{ "id": 1, "title": "2025 General Election", ... }`
   - **Test Cases**:
     - Valid data (success).
     - Invalid dates (400).
     - Non-admin user (403).

2. **List Elections (GET /api/election/list/)**
   - **Headers**: `Authorization: Bearer <user_jwt>`
   - **Expected**: 200, `[{ "id": 1, "title": "2025 General Election", ... }, ...]`
   - **Test Cases**:
     - Authenticated user (success).
     - No token (401).

3. **Vote (POST /api/election/vote/)**
   - **Headers**: `Authorization: Bearer <user_jwt>`
   - **Body**:
     ```json
     {
       "election_id": 1,
       "election_level": 1,
       "candidate_id": 1,
       "token": "uuid-from-voter-token"
     }
     ```
   - **Expected**: 200, `{ "message": "Vote cast" }`
   - **Test Cases**:
     - Valid token, eligible level (success).
     - Used/expired token (400).
     - Ineligible course/state level (403).
     - Election not active (400).

4. **Results (GET /api/election/results/<election_id>/)**
   - **Headers**: `Authorization: Bearer <admin_jwt>`
   - **URL**: `/api/election/results/1/`
   - **Expected**: 200, `[{ "candidate_id": 1, "vote_count": 10, ... }, ...]`
   - **Test Cases**:
     - Admin access (success).
     - Non-admin access (403).
     - Invalid election ID (404).

### Notes
- **Seed Data**: Ensure `ElectionLevel` IDs (1, 2, 3) match president, course, state. Populate `Position`, `Candidate`, and `VoterToken` for testing.
- **Images**: Test candidate image URLs in vote/results responses (e.g., `/media/candidate_images/<filename>`).
- **Celery**: Verify emails are sent (check Celery logs or email service).
- **Edge Cases**: Test token expiration, duplicate votes, and invalid level eligibility.