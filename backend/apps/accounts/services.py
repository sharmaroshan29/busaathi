from django.contrib.auth import get_user_model
from django.db import transaction
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken

from .models import PassengerProfile

User = get_user_model()


@transaction.atomic
def register_passenger(
    *,
    username: str,
    email: str,
    password: str,
    full_name: str = "",
    phone_number: str = "",
):
    """
    Creates a new User and their associated PassengerProfile atomically.
    
    Note: The '*' in the arguments forces callers to use keyword arguments
    (e.g., register_passenger(username=..., email=...)), which prevents
    accidental argument-order bugs across layers!
    """
    # 1. create_user() automatically hashes the password using PBKDF2
    user = User.objects.create_user(
        username=username.strip(),
        email=email.lower().strip(),
        password=password,
        phone_number=phone_number.strip(),
    )

    # 2. Create the linked 1:1 PassengerProfile in the same DB transaction
    PassengerProfile.objects.create(
        user=user,
        full_name=full_name.strip(),
    )

    return user


def logout_user(*, refresh_token: str) -> None:
    """
    Revokes a JWT refresh token by adding it to the database blacklist
    (PRD Section 6.1 & Phase 2 Task 1).
    """
    token = RefreshToken(refresh_token)
    token.blacklist()