from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import SeatHold, BookingSeat
from apps.fleet.models import Seat
from apps.trips.models import Trip


def hold_seats_for_checkout(*, user, trip_id: int, seat_ids: list[int]) -> list[SeatHold]:
    """
    Creates temporary holds for selected seats (PRD Phase 4, Task 4).
    Uses atomic transactions and row-level locks to completely eliminate race conditions.
    """
    # transaction.atomic() ensures that if anything fails, all database changes are rolled back instantly.
    with transaction.atomic():
        # 1. Fetch and lock the specific seats in PostgreSQL
        seats = Seat.objects.select_for_update().filter(
            id__in=seat_ids,
            layout__trips__id=trip_id
        )
        
        if len(seats) != len(seat_ids):
            raise ValidationError("One or more selected seats are invalid for this trip.")

        # 2. Check if seats are already permanently booked
        already_booked = BookingSeat.objects.filter(
            booking__trip_id=trip_id,
            booking__status="confirmed",
            seat__in=seats
        ).exists()
        
        if already_booked:
            raise ValidationError("One or more seats have already been booked.")

        # 3. Check if seats are currently held by another user
        now = timezone.now()
        active_holds = SeatHold.objects.filter(
            trip_id=trip_id,
            seat__in=seats,
            expires_at__gt=now
        )
        
        if active_holds.exists():
            raise ValidationError("One or more seats are currently locked by another passenger.")

        # 4. If all checks pass, generate the new holds
        holds_to_create = [
            SeatHold(user=user, trip_id=trip_id, seat=seat)
            for seat in seats
        ]
        
        return SeatHold.objects.bulk_create(holds_to_create)


def release_expired_holds() -> int:
    """
    Finds and deletes all SeatHolds that have passed their expiration time (PRD Phase 4, Task 5).
    Returns the number of released seats.
    """
    now = timezone.now()
    
    # Find holds where the expiration time is strictly in the past
    expired_holds = SeatHold.objects.filter(expires_at__lte=now)
    
    # Delete them and capture how many rows were affected
    deleted_count, _ = expired_holds.delete()
    
    return deleted_count