from django.urls import path
from . import views

app_name = "bookings"

urlpatterns = [
    path("hold/", views.CreateSeatHoldAPIView.as_view(), name="hold-seats"),
    path("checkout/", views.CheckoutAPIView.as_view(), name="checkout"),
    path("pay/", views.PaymentAPIView.as_view(), name="mock-payment"),
    path("<int:booking_id>/cancel/", views.CancelBookingAPIView.as_view(), name="cancel-booking"),
    path("trip/<int:trip_id>/manifest/", views.TripManifestAPIView.as_view(), name="trip-manifest"),
]