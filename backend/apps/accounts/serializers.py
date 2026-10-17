from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers

from .models import PassengerProfile

User = get_user_model()


class RegisterInputSerializer(serializers.Serializer):
    """
    Validates incoming JSON for POST /api/v1/auth/register/.
    Think of this just like a FastAPI Pydantic BaseModel for request bodies!
    """

    username = serializers.CharField(max_length=150)
    email = serializers.EmailField()
    # write_only=True ensures the password is NEVER included in any outgoing JSON response
    password = serializers.CharField(
        write_only=True,
        min_length=8,
        validators=[validate_password],
    )
    full_name = serializers.CharField(max_length=150, required=False, allow_blank=True, default="")
    phone_number = serializers.CharField(max_length=20, required=False, allow_blank=True, default="")

    def validate_username(self, value: str) -> str:
        """Field-level hook: DRF automatically runs validate_<field_name>."""
        username = value.strip()
        if User.objects.filter(username__iexact=username).exists():
            raise serializers.ValidationError("A user with this username already exists.")
        return username

    def validate_email(self, value: str) -> str:
        """Enforce case-insensitive email uniqueness before hitting the database."""
        email = value.lower().strip()
        if User.objects.filter(email=email).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return email


class PassengerProfileOutputSerializer(serializers.ModelSerializer):
    """Serializes the nested PassengerProfile data."""

    class Meta:
        model = PassengerProfile
        fields = (
            "full_name",
            "date_of_birth",
            "emergency_contact_name",
            "emergency_contact_phone",
        )


class UserOutputSerializer(serializers.ModelSerializer):
    """
    Formats User object into safe outgoing JSON (used in /register/ and /me/).
    Notice 'password' is strictly excluded from fields!
    """

    passenger_profile = PassengerProfileOutputSerializer(read_only=True)

    class Meta:
        model = User
        fields = (
            "id",
            "username",
            "email",
            "phone_number",
            "is_email_verified",
            "is_active",
            "date_joined",
            "passenger_profile",
        )


class LogoutInputSerializer(serializers.Serializer):
    """Validates that a refresh token string is provided when logging out."""

    refresh = serializers.CharField()