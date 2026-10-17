from django.db import models
from apps.trips.models import Trip, TripStop
from apps.fleet.models import Seat
from django.conf import settings
from django.utils import timezone
from datetime import timedelta
import uuid


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


    base_fare =models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00,
        help_text="Snapshot of Seat fare before the tax"
    )
    tax_amount = models.DecimalField(
        max_digits=10, decimal_places=2, default=0.00, 
        help_text="Snapshot of GST / platform fees"
    )
    currency = models.CharField(
        max_length=3, default="INR", 
        help_text="ISO currency code snapshot"
    )
    merchant_account_id = models.CharField(
        max_length=100, default="mock_merch_default",
        help_text="Snapshot of the operator's connected merchant ID for payout routing"
    )
    cancellation_policy = models.TextField(
        default="100% refund if cancelled 24h before departure; 50% refund up to 6h before.",
        help_text="Snapshot of cancellation terms agreed to at checkout"
    )

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


class PaymentTransaction(models.Model):
    """Track Payment Status"""

    class Status(models.TextChoices):
        INITIATED = "initiated", "Initiated"
        SUCCESS = "success", "Success"
        FAILED = "failed", "Failed"
        REFUND_REQUIRED ="refund_required", "Late Payment -Refund required"

    booking  =models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="payments")
    idempotency_key = models.CharField(
        max_length=100, unique=True, db_index=True,
        help_text="Client-generated unique key to prevent duplicate payment creation"
    )
    provider_order_id = models.CharField(max_length=100, unique=True, default=uuid.uuid4)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=25, choices=Status.choices, default=Status.INITIATED)
    
    # Stores raw mock webhook JSON payload for financial reconciliation (PRD Task 9)
    provider_response = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"Order {self.provider_order_id} ({self.status}) - ₹{self.amount}"



class Ticket(models.Model):
    """The final digital ticket only after complet payments"""
    booking =models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="ticket")
    ticket_number =models.CharField(max_length=30, unique=True, db_index=True)
    issued_at =models.DateTimeField(auto_now_add=True)
    is_delivered =models.BooleanField(default=True, help_text="Persistent ticket delivery state")

    def __str__(self) -> str:
        return f"Ticket {self.ticket_number} for PNR {self.booking.pnr}"



class Refund(models.Model):
    """Track all the monney returnedto a user after cancellation"""

    class Status(models.TextChoices):
        PENDING ="pending", "PENDING"
        PROCESSED ="processed", "Processed"
        FAILED ="failed", "Failed"

    booking =models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="refund")
    amount =models.DecimalField(max_digits=10, decimal_places=2)
    reason =models.CharField(max_length=255)
    status =models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at =models.DateTimeField(auto_now_add=True)
    updated_at =models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Refund for {self.booking.pnr} - {self.amount}"

class SettlementBatch(models.Model):
    """PRD Task 4: Groups multiple SettlementItems into a single payout transfer."""
    
    class Status(models.TextChoices):
        PROCESSING = "processing", "Processing Transfer"
        PAID = "paid", "Paid to Operator"
        FAILED = "failed", "Transfer Failed"

    operator = models.ForeignKey("operators.Operator", on_delete=models.PROTECT, related_name="batches")
    batch_reference = models.CharField(max_length=50, unique=True, help_text="Bank UTR or transfer reference")
    total_payout = models.DecimalField(max_digits=12, decimal_places=2, default=0.00)
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PROCESSING)
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return f"Batch {self.batch_reference} - {self.operator.name} ({self.total_payout})"



class SettlementItem(models.Model):
    """PRD Task 3 & 4: Records the financial split and settlement status for a confirmed booking."""
    
    class Status(models.TextChoices):
        PENDING = "pending", "Pending (Unpaid to Operator)"
        SETTLED = "settled", "Settled (Paid to Operator)"

    # Link to the specific booking and the operator owed
    booking = models.OneToOneField(Booking, on_delete=models.CASCADE, related_name="settlement")
    operator = models.ForeignKey("operators.Operator", on_delete=models.PROTECT, related_name="settlements")
    batch = models.ForeignKey(SettlementBatch, on_delete=models.SET_NULL, null=True, blank=True, related_name="items")
    # Financial Split
    total_amount = models.DecimalField(max_digits=10, decimal_places=2, help_text="Total fare collected from passenger")
    platform_commission = models.DecimalField(max_digits=10, decimal_places=2, help_text="BuSaathi's cut")
    operator_payable = models.DecimalField(max_digits=10, decimal_places=2, help_text="Amount owed to the operator")
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.PENDING)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Settlement for {self.booking.pnr} - Owed: {self.operator_payable}"


