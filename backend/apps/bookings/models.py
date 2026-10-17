from django.db import models
from apps.trips.models import Trip, TripStop
from apps.fleet.models import Seat
from django.conf import settings
from django.utils import timezone
from datetime import timedelta

class Booking(models.Model):
    """The master reservation record for a transaction."""

    class Status(models.TextChoices):
        PENDING = "pending", "Pending Payment"
        CONFIRMED = "confirmed", "Confirmed"
        CANCELLED = "cancelled", "Cancelled"

    # Generates an 8-character alphanumeric PNR (e.g., 'X7B9K2M1')
    pnr = models.CharField(max_length=15, unique=True, db_index=True, help_text="Passenger Name Record")
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="bookings")
    trip = models.ForeignKey(Trip, on_delete=models.PROTECT, related_name="bookings")
    
    # Passengers board and drop at specific trip stops, not just the route origin/destination
    boarding_stop = models.ForeignKey(TripStop, on_delete=models.PROTECT, related_name="boarding_bookings")
    drop_stop = models.ForeignKey(TripStop, on_delete=models.PROTECT, related_name="drop_bookings")
    
    total_fare = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total amount in INR")
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"PNR: {self.pnr} - {self.status}"


class BookingSeat(models.Model):
    """Tracks the individual passenger details for a specific booked seat."""

    class Gender(models.TextChoices):
        MALE = "M", "Male"
        FEMALE = "F", "Female"
        OTHER = "O", "Other"

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="seats")
    seat = models.ForeignKey(Seat, on_delete=models.PROTECT)
    
    passenger_name = models.CharField(max_length=150)
    passenger_age = models.PositiveIntegerField()
    passenger_gender = models.CharField(max_length=1, choices=Gender.choices)
    seat_fare = models.DecimalField(max_digits=8, decimal_places=2, help_text="Individual seat price")

    def __str__(self) -> str:
        return f"{self.passenger_name} ({self.seat.seat_number})"

    

def default_hold_expiry():
    """Generates an expiry time 10 minutes from now."""
    return timezone.now() + timedelta(minutes=10)

class SeatHold(models.Model):
    """
    Temporary lock on a seat during the checkout process (PRD Phase 4, Task 4).
    Prevents double-booking by reserving the seat for 10 minutes before payment.
    """
    
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="seat_holds")
    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="seat_holds")
    seat = models.ForeignKey(Seat, on_delete=models.CASCADE)
    
    expires_at = models.DateTimeField(default=default_hold_expiry)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        # We index these fields because our Search API will query them heavily 
        # to calculate real-time seat availability (PRD Phase 4, Task 3).
        indexes = [
            models.Index(fields=["trip", "seat", "expires_at"]),
        ]

    def __str__(self) -> str:
        return f"Hold: {self.seat.seat_number} on Trip {self.trip.id} (Expires: {self.expires_at.strftime('%H:%M')})"
    
    @property
    def is_active(self) -> bool:
        """Helper to quickly check if the hold is still valid."""
        return timezone.now() < self.expires_at
# Create your models here.
