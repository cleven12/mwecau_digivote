# core/views.py
from datetime import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
import requests
from django.urls import reverse
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class APIHealthCheckView(APIView):
    """API endpoint to check the health of all API endpoints."""
    permission_classes = [AllowAny]  # Allow public access for health checks

    def get(self, request):
        base_url = f"{request.scheme}://{request.get_host()}"
        health_data = {
            "status": "healthy",
            "endpoints": {},
            "timestamp": timezone.now().isoformat(),
            "environment": "development" if settings.DEBUG else "production"
        }

        # Helper function to check endpoint
        def check_endpoint(method, url, requires_auth=False, payload=None, expected_status=200):
            try:
                headers = {}
                if requires_auth:
                    # For simplicity, skip actual auth token generation; assume endpoint is reachable
                    headers['Authorization'] = 'Bearer mock_token'
                response = requests.request(
                    method,
                    f"{base_url}{url}",
                    json=payload,
                    headers=headers,
                    timeout=5
                )
                is_healthy = response.status_code == expected_status
                return {
                    "status": "healthy" if is_healthy else "unhealthy",
                    "status_code": response.status_code,
                    "message": "OK" if is_healthy else response.text[:100]
                }
            except requests.RequestException as e:
                logger.error(f"Health check failed for {url}: {str(e)}")
                return {
                    "status": "unhealthy",
                    "status_code": None,
                    "message": f"Request failed: {str(e)}"
                }

        # Authentication Endpoints
        health_data["endpoints"]["auth_login"] = check_endpoint(
            method="POST",
            url=reverse("core:api_login"),
            payload={"registration_number": "TEST/001", "password": "test"},
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without valid credentials
        )
        health_data["endpoints"]["auth_logout"] = check_endpoint(
            method="POST",
            url=reverse("core:api_logout"),
            payload={"refresh": "mock_refresh_token"},
            requires_auth=True,
            expected_status=status.HTTP_400_BAD_REQUEST  # Expect failure without valid token
        )
        health_data["endpoints"]["auth_refresh"] = check_endpoint(
            method="POST",
            url=reverse("core:api_token_refresh"),
            payload={"refresh": "mock_refresh_token"},
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without valid token
        )
        health_data["endpoints"]["auth_register"] = check_endpoint(
            method="POST",
            url=reverse("core:api_register"),
            payload={"registration_number": "TEST-001"},
            expected_status=status.HTTP_404_NOT_FOUND  # Expect failure if reg number doesn't exist
        )
        health_data["endpoints"]["auth_complete_registration"] = check_endpoint(
            method="POST",
            url=reverse("core:api_complete_registration"),
            payload={
                "registration_number": "TEST-001",
                "email": "test@example.com",
                "password": "Test@1234",
                "password_confirm": "Test@1234",
                "state": 1,
                "course": 1
            },
            expected_status=status.HTTP_404_NOT_FOUND  # Expect failure if college data not found
        )
        health_data["endpoints"]["auth_forgot_password"] = check_endpoint(
            method="POST",
            url=reverse("core:api_forgot_password"),
            payload={
                "registration_number": "TEST-001",
                "email": "test@example.com",
                "state": 1,
                "course": 1
            },
            expected_status=status.HTTP_404_NOT_FOUND  # Expect failure if user not found
        )
        health_data["endpoints"]["auth_password_reset_confirm"] = check_endpoint(
            method="POST",
            url=reverse("core:api_password_reset_confirm"),
            payload={"token": "mock_token", "new_password": "NewPass@123"},
            expected_status=status.HTTP_400_BAD_REQUEST  # Expect failure with invalid token
        )
        health_data["endpoints"]["auth_verify_request"] = check_endpoint(
            method="POST",
            url=reverse("core:api_verification_request"),
            requires_auth=True,
            expected_status=status.HTTP_400_BAD_REQUEST  # Expect failure without valid user
        )
        health_data["endpoints"]["auth_verify_user"] = check_endpoint(
            method="POST",
            url=reverse("core:api_verify_user"),
            payload={"registration_number": "TEST-001"},
            requires_auth=True,
            expected_status=status.HTTP_403_FORBIDDEN  # Expect failure without commissioner role
        )
        health_data["endpoints"]["auth_verify_status"] = check_endpoint(
            method="GET",
            url=reverse("core:api_verification_status"),
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["auth_dashboard"] = check_endpoint(
            method="GET",
            url=reverse("core:api_dashboard"),
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["auth_update_profile"] = check_endpoint(
            method="PUT",
            url=reverse("core:api_update_profile"),
            payload={"email": "new@example.com", "state": 1},
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["auth_change_password"] = check_endpoint(
            method="POST",
            url=reverse("core:api_change_password"),
            payload={"old_password": "old", "new_password": "new"},
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["auth_contact_commissioner"] = check_endpoint(
            method="POST",
            url=reverse("core:api_contact_commissioner"),
            payload={"message": "Test message"},
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )

        # Reference Data Endpoints
        health_data["endpoints"]["states"] = check_endpoint(
            method="GET",
            url=reverse("core:api_states"),
            expected_status=status.HTTP_200_OK
        )
        health_data["endpoints"]["courses"] = check_endpoint(
            method="GET",
            url=reverse("core:api_courses"),
            expected_status=status.HTTP_200_OK
        )

        # Election Endpoints
        health_data["endpoints"]["election_list"] = check_endpoint(
            method="GET",
            url=reverse("election_list"),
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["election_vote"] = check_endpoint(
            method="POST",
            url=reverse("api_vote"),
            payload={"voter_token": "mock_token", "candidate_id": 1},
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["election_results"] = check_endpoint(
            method="GET",
            url=reverse("api_results", kwargs={"election_id": 1}),
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )

        # Admin Endpoints (assuming they exist based on documentation)
        health_data["endpoints"]["users_list"] = check_endpoint(
            method="GET",
            url="/api/users/",  # Not defined in provided URLs, assuming based on docs
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["users_me"] = check_endpoint(
            method="GET",
            url="/api/users/me/",
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["college_data"] = check_endpoint(
            method="GET",
            url="/api/college-data/",
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )
        health_data["endpoints"]["college_data_bulk_upload"] = check_endpoint(
            method="POST",
            url="/api/college-data/bulk-upload/",
            requires_auth=True,
            expected_status=status.HTTP_401_UNAUTHORIZED  # Expect failure without auth
        )

        # Check if any endpoint is unhealthy
        if any(endpoint_data["status"] == "unhealthy" for endpoint_data in health_data["endpoints"].values()):
            health_data["status"] = "unhealthy"

        return Response(health_data, status=status.HTTP_200_OK)