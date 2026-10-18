from django.db import DatabaseError, connection
from django.http import JsonResponse
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import (
    LogoutInputSerializer,
    RegisterInputSerializer,
    UserOutputSerializer,
)
from .services import logout_user, register_passenger
from django.contrib.auth.models import User
from google.oauth2 import id_token
from google.auth.transport import requests
import os


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()

        return JsonResponse(
            {"status": "ok", "database": "connected"},
            status=200,
        )
    except DatabaseError:
        return JsonResponse(
            {"status": "error", "database": "disconnected"},
            status=503,
        )

class RegisterAPIView(APIView):
    """
    POST /api/v1/auth/register/
    Public endpoint to register a new passenger account and return initial JWT tokens.
    """

    # Override global IsAuthenticated setting so new visitors can sign up
    permission_classes = [AllowAny]

    def post(self, request):
        # 1. Validate incoming JSON (automatically returns 400 Bad Request if invalid)
        serializer = RegisterInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        # 2. Execute domain workflow via service layer
        user = register_passenger(**serializer.validated_data)

        # 3. Generate initial JWT access & refresh tokens so user is logged in immediately
        refresh = RefreshToken.for_user(user)

        return Response(
            {
                "user": UserOutputSerializer(user).data,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            },
            status=status.HTTP_201_CREATED,
        )


class MeAPIView(APIView):
    """
    GET /api/v1/auth/me/
    Returns the currently authenticated user's profile.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        # DRF's JWTAuthentication middleware automatically sets request.user
        # from the 'Authorization: Bearer <access_token>' header!
        return Response(UserOutputSerializer(request.user).data, status=status.HTTP_200_OK)


class LogoutAPIView(APIView):
    """
    POST /api/v1/auth/logout/
    Blacklists the user's refresh token so no further access tokens can be minted.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = LogoutInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            logout_user(refresh_token=serializer.validated_data["refresh"])
        except TokenError:
            return Response(
                {"detail": "Token is invalid or already blacklisted."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        return Response(status=status.HTTP_204_NO_CONTENT)



class GoogleLoginView(APIView):
    """Recieve Google ID token from the frontend verifies it. 
    Gets or creates the user , and return s BuSaathi JWT Tokens"""

    def post(self, request):
        token =request.data.get('credential')
        if not token:
            return Response({'error': 'No Google credential provided'}, status=status.HTTP_400_BAD_REQUEST)
        try:
            # Verify the token against Google's public keys
            # Replace YOUR_GOOGLE_CLIENT_ID with your actual Google OAuth Client ID
            CLIENT_ID = os.environ.get('GOOGLE_CLIENT_ID')
            idinfo = id_token.verify_oauth2_token(token, requests.Request(), CLIENT_ID)

            email = idinfo['email']
            name = idinfo.get('name', '')
            first_name = idinfo.get('given_name', '')
            last_name = idinfo.get('family_name', '')

            # Get or create the user in PostgreSQL
            user, created = User.objects.get_or_create(
                email=email,
                defaults={
                    'username': email,
                    'first_name': first_name,
                    'last_name': last_name
                }
            )

            # Issue standard SimpleJWT tokens for session management
            refresh = RefreshToken.for_user(user)
            
            return Response({
                'refresh': str(refresh),
                'access': str(refresh.access_token),
                'user': {
                    'email': user.email,
                    'name': f"{user.first_name} {user.last_name}".strip()
                }
            }, status=status.HTTP_200_OK)

        except ValueError as e:
            return Response({'error': f'Invalid Google Token: {str(e)}'}, status=status.HTTP_400_BAD_REQUEST)




