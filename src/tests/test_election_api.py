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