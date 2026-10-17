from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from .models import SeatHold, BookingSeat, Booking, Refund, SettlementBatch
from apps.fleet.models import Seat
from apps.trips.models import Trip
from .models import PaymentTransaction, Ticket, SettlementItem
from django.db.models import Sum
from decimal import Decimal
import uuid



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



from apps.trips.models import FareRule

@transaction.atomic
def create_booking_from_hold(user, trip_id: int, seat_ids: list, boarding_stop_id: int, drop_stop_id: int) -> Booking:
    """
    PRD Task 1 & 2: Converts active SeatHolds into a PENDING Booking 
    while snapshotting fares, taxes, currency, and cancellation policies.
    """
    now = timezone.now()

    # 1. Verify that non-expired holds exist for this user and these exact seats
    holds = SeatHold.objects.select_for_update().filter(
        user=user,
        trip_id=trip_id,
        seat_id__in=seat_ids,
        expires_at__gt=now
    )

    if holds.count() != len(seat_ids):
        raise ValidationError("Some selected seats have expired or are no longer locked by you.")

    trip = holds[0].trip

    # Helper to look up seat price from FareRule for this trip
    def get_seat_price(seat_obj):
        rule = FareRule.objects.filter(trip=trip, seat_type=seat_obj.seat_type, deck=seat_obj.deck).first()
        return rule.price if rule else Decimal("500.00")

    # 2. Calculate financial totals and snapshot fares
    base_fare_total = sum(get_seat_price(h.seat) for h in holds)
    tax_amount = (base_fare_total * Decimal("0.05")).quantize(Decimal("0.01"))  # 5% GST snapshot
    total_fare = base_fare_total + tax_amount

    # Generate a unique PNR
    pnr_code = f"BS-{uuid.uuid4().hex[:6].upper()}"

    # 3. Create the master Booking record with financial snapshots (PRD Task 2 & 4)
    booking = Booking.objects.create(
        pnr=pnr_code,
        user=user,
        trip=trip,
        boarding_stop_id=boarding_stop_id,
        drop_stop_id=drop_stop_id,
        base_fare=base_fare_total,
        tax_amount=tax_amount,
        total_fare=total_fare,
        currency="INR",
        merchant_account_id=getattr(trip.operator, "merchant_id", "mock_merch_default"),
        status=Booking.Status.PENDING
    )

    # 4. Create individual BookingSeat records and clear out the temporary holds
    for hold in holds:
        BookingSeat.objects.create(
            booking=booking,
            seat=hold.seat,
            passenger_name=getattr(user, "full_name", "") or user.email,
            passenger_age=22,
            passenger_gender="M",
            seat_fare=get_seat_price(hold.seat)
        )

    # Delete the temporary holds since they are now converted into a booking
    holds.delete()

    return booking

@transaction.atomic
def process_mock_payment(booking_id: int, idempotency_key: str, outcome: str = "SUCCESS") -> PaymentTransaction:
    """
    Processes an idempotent payment transaction 
    and triggers state-machine logic upon webhook confirmation.
    """
    booking = Booking.objects.select_for_update().get(pk=booking_id)

    # 1. Idempotency Check (PRD Task 5): If this idempotency key was already processed, return it instantly!
    existing_txn = PaymentTransaction.objects.filter(idempotency_key=idempotency_key).first()
    if existing_txn:
        return existing_txn

    # 2. Create the initial payment transaction record
    payment_txn = PaymentTransaction.objects.create(
        booking=booking,
        idempotency_key=idempotency_key,
        amount=booking.total_fare,
        status=PaymentTransaction.Status.INITIATED
    )

    # 3. Handle Webhook / Gateway Outcome State Machine (PRD Tasks 6, 7, 8, 9)
    if outcome == "SUCCESS":
        # Check if booking is still valid / not expired or cancelled
        if booking.status == Booking.Status.PENDING:
            payment_txn.status = PaymentTransaction.Status.SUCCESS
            payment_txn.provider_response = {"gateway": "mock", "status": "captured", "reason": "success"}
            payment_txn.save()

            # Confirm the booking
            booking.status = Booking.Status.CONFIRMED
            booking.save()

            # Issue a unique digital ticket (PRD Task 8)
            ticket_num = f"TKT-{timezone.now().strftime('%Y%m%d')}-{booking.pnr}"
            Ticket.objects.create(
                booking=booking,
                ticket_number=ticket_num,
                is_delivered=True
            )

            # --- NEW: Phase 6 Task 3 Commission Logic ---
            # 1. Define BuSaathi's commission rate (e.g., 5%)
            commission_rate = Decimal('0.05')
            
            # 2. Calculate the exact splits from the booking's total_fare
            platform_cut = (booking.total_fare * commission_rate).quantize(Decimal("0.01"))
            operator_cut = booking.total_fare - platform_cut
            
            # 3. Create the immutable ledger record
            SettlementItem.objects.create(
                booking=booking,
                operator=booking.trip.operator,
                total_amount=booking.total_fare,
                platform_commission=platform_cut,
                operator_payable=operator_cut
            )

        else:
            # Late Payment Recovery (PRD Task 9): Payment succeeded, but hold/booking expired!
            payment_txn.status = PaymentTransaction.Status.REFUND_REQUIRED
            payment_txn.provider_response = {"gateway": "mock", "reason": "late_payment_expired_booking"}
            payment_txn.save()
            raise ValidationError("Payment arrived after booking expiration. Flagged for automatic refund.")

    elif outcome == "FAILED":
        payment_txn.status = PaymentTransaction.Status.FAILED
        payment_txn.provider_response = {"gateway": "mock", "reason": "card_declined"}
        payment_txn.save()
        # Leave booking as pending or mark expired

    return payment_txn



@transaction.atomic
def cancel_booking(user, booking_id:int) -> Booking:
    """Cancels the booking free up the seats, and calculates the fair """


    booking =Booking.objects.select_for_update().get(id=booking_id, user=user)
    if booking.status==Booking.Status.CANCELLED:
        raise ValidationError("This Booking is already cancelled")

    now =timezone.now()
    departure_time =booking.trip.departure_time
    time_left =departure_time-now

    if time_left.total_seconds()<=0:
        raise ValidationError("Trip has already departed, no cancellation available")
    
    hours_left =time_left.total_seconds()/3600

    if hours_left>=24:
        refund_percentage =Decimal('1.00')
    elif 6<=hours_left<24:
        refund_percentage =Decimal('0.50')
    else:
        refund_percentage =Decimal("0.00")

    refund_amount =booking.total_fare*refund_percentage
    booking.status =Booking.Status.CANCELLED
    booking.save()

    if refund_amount>0:
        Refund.objects.create(
            booking =booking,
            amount =refund_amount,
            reason =f"User Cancellation {int(hours_left)} ours before departure"
        )

    return booking


@transaction.atomic
def generate_operator_payout_batch(operator_id: int) -> SettlementBatch:
    """
    Finds all 'pending' SettlementItems for an operator and groups them into a processing batch.
    """
    # 1. Lock all pending settlement items for this operator to prevent race conditions
    pending_items = SettlementItem.objects.select_for_update().filter(
        operator_id=operator_id,
        status=SettlementItem.Status.PENDING,
        batch__isnull=True
    )

    if not pending_items.exists():
        raise ValidationError("No pending settlements found for this operator.")

    # 2. Calculate the total payout amount
    total_owed = pending_items.aggregate(total=Sum('operator_payable'))['total']

    # 3. Create the Batch record
    batch = SettlementBatch.objects.create(
        operator_id=operator_id,
        batch_reference=f"PAY-{uuid.uuid4().hex[:8].upper()}",
        total_payout=total_owed,
        status=SettlementBatch.Status.PROCESSING
    )

    # 4. Link the items to the batch and mark them as settled
    pending_items.update(
        batch=batch,
        status=SettlementItem.Status.SETTLED
    )

    return batch




