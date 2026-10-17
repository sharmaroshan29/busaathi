from django.core.exceptions import ValidationError
from django.utils import timezone
from .models import Trip


def publish_trip(*, trip_id: int) -> Trip:
    """
    Business logic to transition a Trip from DRAFT to PUBLISHED.
    Enforces Phase 3, Task 7 PRD constraints before allowing publication.
    """
    try:
        trip = Trip.objects.get(id=trip_id)
    except Trip.DoesNotExist:
        raise ValidationError("Trip does not exist.")

    if trip.status != Trip.Status.DRAFT:
        raise ValidationError(f"Only DRAFT trips can be published. Current status is {trip.status}.")

    # 1. Validation: Trip must be in the future
    if trip.departure_time <= timezone.now():
        raise ValidationError("Cannot publish a trip with a past departure time.")

    # 2. Validation: Trip must have at least one fare rule set
    if not trip.fare_rules.exists():
        raise ValidationError("Cannot publish a trip without any Fare Rules.")

    # 3. Validation: The assigned operator must be ACTIVE
    if trip.operator.status != "active":
        raise ValidationError("Cannot publish a trip for an inactive or suspended operator.")

    # 4. Validation: Operator must have a linked payment profile
    if not hasattr(trip.operator, 'payment_profile') or trip.operator.payment_profile.payout_status != "active":
        raise ValidationError("Operator must have an active payment profile to publish trips.")

    # All checks passed! Transition state and save.
    trip.status = Trip.Status.PUBLISHED
    trip.save(update_fields=["status", "updated_at"])
    
    return trip