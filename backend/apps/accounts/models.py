
from django.contrib.auth.models import AbstractUser


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

    def __str__(self) -> str:
        # A readable representation for Django Admin and debugging.
        return self.username
