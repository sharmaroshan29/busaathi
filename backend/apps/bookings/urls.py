from django.urls import path
from . import views

app_name = "bookings"

urlpatterns = [
    path("hold/", views.CreateSeatHoldAPIView.as_view(), name="hold-seats"),
]