from django.urls import path
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from . import views


app_name ="accounts"

urlpatterns = [
    path("health/", views.health_check, name="health-check"),
    path("register/", views.RegisterAPIView.as_view(), name="register"),
    path("me/", views.MeAPIView.as_view(), name="me"),
    path("logout/", views.LogoutAPIView.as_view(), name="logout"),
    # SimpleJWT Built-in Views (checks username/password + is_active and returns JWT pair)
    path("login/", TokenObtainPairView.as_view(), name="login"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token-refresh"),
    path('auth/google/', views.GoogleLoginView.as_view(), name='google-login'),


]

