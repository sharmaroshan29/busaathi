from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
from django.contrib.auth import get_user_model
from .models import Operator, OperatorMembership

User = get_user_model()


class CrossTenantSecurityTests(APITestCase):
    """
    Phase 2 (Sub-section 2.4) Security Tests:
    Verifies that Operator A cannot access or modify Operator B's tenant resources.
    """

    def setUp(self):
        # 1. Create two separate users
        self.user_a = User.objects.create_user(username="owner_a", email="a@example.com", password="Password123!")
        self.user_b = User.objects.create_user(username="owner_b", email="b@example.com", password="Password123!")

        # 2. Create two separate operators
        self.operator_a = Operator.objects.create(name="Awadh Express", slug="awadh-express", contact_email="a@awadh.com", contact_phone="1111111111", status=Operator.Status.ACTIVE)
        self.operator_b = Operator.objects.create(name="Zingbus", slug="zingbus", contact_email="b@zingbus.com", contact_phone="2222222222", status=Operator.Status.ACTIVE)

        # 3. Link User A to Operator A as Owner
        OperatorMembership.objects.create(user=self.user_a, operator=self.operator_a, role=OperatorMembership.Role.OWNER, status=OperatorMembership.Status.ACTIVE)

        # 4. Link User B to Operator B as Owner
        OperatorMembership.objects.create(user=self.user_b, operator=self.operator_b, role=OperatorMembership.Role.OWNER, status=OperatorMembership.Status.ACTIVE)

    def test_operator_member_permission_blocks_cross_tenant_access(self):
        """Proves that a user belonging to Operator A is blocked when trying to access Operator B."""
        from apps.operators.permissions import IsOperatorMember
        from rest_framework.test import APIRequestFactory

        factory = APIRequestFactory()
        request = factory.get("/")
        request.user = self.user_a  # Logged in as User A (Awadh Express)

        permission = IsOperatorMember()

        # User A has permission to access Operator A -> True
        self.assertTrue(permission.has_object_permission(request, None, self.operator_a))

        # User A MUST NOT have permission to access Operator B -> False (Cross-tenant leak prevented!)
        self.assertFalse(permission.has_object_permission(request, None, self.operator_b))