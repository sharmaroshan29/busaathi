from django.db import models
from django.conf import settings
import uuid

# Create your models here.


class Operator(models.Model):
    """Represent Independent Bus Company on the platform BuSaathi
        Example BSRTC, UPSRTC 
    """

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Verification"
        ACTIVE = "active", "Active"
        REJECTED = "rejected", "Rejected"
        SUSPENDED = "suspended", "Suspended"

    name =models.CharField(max_length=150, unique=True)
    slug =models.SlugField(max_length=160, unique=True)
    contact_email =models.EmailField()
    contact_phone =models.CharField(max_length=10)
    status =models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING
    )
    merchant_id = models.CharField(max_length=100, default="merch_default_id", help_text="Mock merchant account ID for payouts")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self)-> str:
        return f"{self.name} ({self.status})"


class OperatorMembership(models.Model):
    """Linking an user to an Operator with a specific role,
        Control who belongs to which bus company..
    """
    class Role(models.TextChoices):
        OWNER = "owner", "Operator Owner"
        MANAGER = "manager", "Operator Manager"
        STAFF = "staff", "Operator Staff"

    class Status(models.TextChoices):
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    # One user can belong to many operators
    user =models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="operator_memberships",
    )

    # One operators can have many team members
    operator = models.ForeignKey(
        Operator,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    role =models.CharField(max_length=20, choices=Role.choices)
    status =models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.ACTIVE,
    )

    class Meta:

        # Prevent the same user from being added twice to the same operator
        constraints =[
            models.UniqueConstraint(
                fields=["user", "operator"],
                name="unique_user_operator_membership",
            )
        ]

        def __str__(self) -> str:
            return f"{self.user.username} -> {self.operator.name} ({self.role})"


class OperatorInvitation(models.Model):
    """Invitation sent to an user to join an operators team
    """

    class Role(models.TextChoices):
        MANGER ="manager", "Operator Manager"
        STAFF ="staff", "Operator Staff"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending"
        ACCEPTED = "accepted", "Accepted"
        EXPIRED = "expired", "Expired"
        REVOKED = "revoked", "Revoked"

    operator = models.ForeignKey(
        Operator,
        on_delete=models.CASCADE,
        related_name="invitations",
    )

    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    email = models.EmailField(help_text="Email address of the person being invited.")
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.STAFF)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    expires_at = models.DateTimeField()
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"Invite {self.email} -> {self.operator.name} ({self.role})"


class OperatorDocument(models.Model):
    """
    Stores verification document metadata for an operator (PRD Phase 3, Task 2).
    Examples: GST Certificate, PAN Card, Transport License.
    """

    class DocType(models.TextChoices):
        GST_CERTIFICATE = "gst", "GST Certificate"
        PAN_CARD = "pan", "PAN Card"
        LICENSE = "license", "Operating License"
        OTHER = "other", "Other Document"

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Verification"
        VERIFIED = "verified", "Verified"
        REJECTED = "rejected", "Rejected"

    operator = models.ForeignKey(
        Operator,
        on_delete=models.CASCADE,
        related_name="documents",
    )
    doc_type = models.CharField(max_length=30, choices=DocType.choices)
    file_url = models.URLField(max_length=500, help_text="Secure URL to stored document file.")
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.PENDING,
    )
    rejection_reason = models.TextField(blank=True, help_text="Reason if document is rejected.")
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.operator.name} - {self.doc_type} ({self.status})"


class OperatorPaymentProfile(models.Model):
    """
    Tracks payout readiness separately from platform approval (PRD Phase 3, Task 3).
    """

    class PayoutStatus(models.TextChoices):
        UNLINKED = "unlinked", "Unlinked"
        PENDING = "pending", "Pending Verification"
        ACTIVE = "active", "Active"
        SUSPENDED = "suspended", "Suspended"

    operator = models.OneToOneField(
        Operator,
        on_delete=models.CASCADE,
        related_name="payment_profile",
    )
    gateway_account_id = models.CharField(
        max_length=100,
        blank=True,
        help_text="Connected merchant account ID (e.g., Razorpay/Stripe ID).",
    )
    payout_status = models.CharField(
        max_length=20,
        choices=PayoutStatus.choices,
        default=PayoutStatus.UNLINKED,
    )
    bank_details_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Payment Profile for {self.operator.name} [{self.payout_status}]"