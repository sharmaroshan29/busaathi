from django.conf import settings
from django.db import models


class AuditLog(models.Model):
    """
    Immutable audit trail for sensitive actions (PRD Phase 2, Task 6).
    Tracks who did what, when, and from what IP address.
    """

    # Nullable because some system events happen automatically without a logged-in user session
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="audit_logs",
    )
    action = models.CharField(max_length=255, help_text="Short description, e.g., 'OPERATOR_APPROVED'")
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    # JSONField lets us store arbitrary context (e.g., {"operator_id": 5, "old_status": "pending"})
    details = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        actor_name = self.actor.username if self.actor else "System"
        return f"[{self.created_at}] {actor_name} -> {self.action}"