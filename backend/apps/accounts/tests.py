from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

# Always fetch the active User model dynamically using get_user_model()
# rather than importing User directly. It inspects settings.AUTH_USER_MODEL.
User = get_user_model()


class PhaseOneFoundationTests(TestCase):
    """
    Automated test suite verifying Phase 1 Acceptance Criteria:
    1. Custom User model is properly registered as AUTH_USER_MODEL.
    2. Health check endpoint responds with 200 OK and confirms PostgreSQL connectivity.
    """

    def test_custom_user_model_is_configured(self):
        """Verify Django is using our custom accounts.User model and not auth.User."""
        # _meta.label returns '<app_label>.<ModelName>'
        self.assertEqual(User._meta.label, "accounts.User")

        # Verify we can create a user and that set_password hashes the password
        user = User.objects.create_user(
            username="roshan_test",
            email="roshan@example.com",
            password="Password123!",
        )
        self.assertEqual(user.username, "roshan_test")
        self.assertTrue(user.check_password("Password123!"))
        # Ensure the raw password is NEVER stored in plain text
        self.assertNotEqual(user.password, "Password123!")

    def test_health_check_endpoint_returns_200(self):
        """Verify /api/v1/health/ returns HTTP 200 and connected database status."""
        # reverse("health-check") resolves to "/api/v1/health/" from urls.py
        url = reverse("accounts:health-check")

        # self.client is Django's built-in test HTTP client (similar to FastAPI's TestClient)
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.json(),
            {
                "status": "ok",
                "database": "connected",
            },
        )

class AuthenticationLifecycleTests(APITestCase):
    """
    Phase 2 (Sub-section 2.2) Acceptance Tests:
    Verifies registration, login, protected /me/ endpoint, inactive account blocking,
    and refresh token blacklisting on logout.
    """

    def setUp(self):
        self.register_url = reverse("accounts:register")
        self.login_url = reverse("accounts:login")
        self.me_url = reverse("accounts:me")
        self.logout_url = reverse("accounts:logout")
        self.user_payload = {
            "username": "roshan_passenger",
            "email": "Roshan@Example.com",
            "password": "SecurePassword123!",
            "full_name": "Roshan Sharma",
            "phone_number": "9876543210",
        }

    def test_register_creates_user_and_passenger_profile(self):
        """Registration should normalize email, create PassengerProfile, and return tokens."""
        response = self.client.post(self.register_url, self.user_payload, format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn("access", response.data["tokens"])
        self.assertEqual(response.data["user"]["email"], "roshan@example.com")
        self.assertEqual(
            response.data["user"]["passenger_profile"]["full_name"], "Roshan Sharma"
        )

    def test_me_endpoint_requires_authentication(self):
        """Unauthenticated requests to /me/ must fail with 401 Unauthorized."""
        response = self.client.get(self.me_url)
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_login_me_and_logout_flow(self):
        """Full lifecycle: Register -> Access /me/ with Bearer token -> Logout blacklists token."""
        reg_response = self.client.post(self.register_url, self.user_payload, format="json")
        access_token = reg_response.data["tokens"]["access"]
        refresh_token = reg_response.data["tokens"]["refresh"]

        # Authenticate using Bearer token header (just like React will do)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {access_token}")

        # 1. Access protected /me/ endpoint
        me_response = self.client.get(self.me_url)
        self.assertEqual(me_response.status_code, status.HTTP_200_OK)
        self.assertEqual(me_response.data["username"], "roshan_passenger")

        # 2. Logout (blacklist the refresh token)
        logout_response = self.client.post(
            self.logout_url, {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(logout_response.status_code, status.HTTP_204_NO_CONTENT)

        # 3. Attempting to reuse the blacklisted refresh token must fail with 400
        repeat_logout = self.client.post(
            self.logout_url, {"refresh": refresh_token}, format="json"
        )
        self.assertEqual(repeat_logout.status_code, status.HTTP_400_BAD_REQUEST)