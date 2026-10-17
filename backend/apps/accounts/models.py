
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from django.db import models



class User(AbstractUser):
    """
    BuSaathi's user identity.

    We extend Django's built-in user rather than implementing
    password storage and authentication from scratch.

    A user can later act as a passenger, operator staff member,
    or platform administrator through separate domain relationships
    and permissions.
    """

    # AbstractUser already provides username, password, email,
    # first_name, last_name, is_active, and other auth fields.
    # We intentionally keep this model minimal for now.
    email =models.EmailField(unique=True)
    phone_number =models.CharField(max_length=10, blank=True)
    is_email_verified =models.BooleanField(default=False)
    updated_at =models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        if self.email:
            self.email =self.email.lower().strip()
        super().save(*args, **kwargs)

    
    def __str__(self) -> str:
        # A readable representation for Django Admin and debugging.
        return f"{self.username} ({self.email})"


class PassengerProfile(models.Model):
        """Optional passenger only profile data"""

        user =models.OneToOneField(
            settings.AUTH_USER_MODEL,
            on_delete=models.CASCADE,
            related_name="passenger_profile"
        )

        full_name = models.CharField(max_length=150, blank=True)
        date_of_birth = models.DateField(null=True, blank=True)
        emergency_contact_name = models.CharField(max_length=150, blank=True)
        emergency_contact_phone = models.CharField(max_length=20, blank=True)
        created_at = models.DateTimeField(auto_now_add=True)
        updated_at = models.DateTimeField(auto_now=True)


        def __str__(self) -> str:
            return f"Passenger profile for {self.user.username}"

