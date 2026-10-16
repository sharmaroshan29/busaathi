from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

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