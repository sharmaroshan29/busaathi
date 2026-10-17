
from django.db import models
from apps.operators.models import Operator
from apps.routes.models import Route, RouteStop
from apps.fleet.models import Bus, SeatLayout, Seat


class Trip(models.Model):
    """A specific scheduled journey of a bus along a route (PRD Phase 3, Tasks 6 & 7)."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        CANCELLED = "cancelled", "Cancelled"

    operator = models.ForeignKey(Operator, on_delete=models.CASCADE, related_name="trips")
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="trips")
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name="trips")
    
    # PRD Constraint: Trip configuration retains its seat-layout version
    seat_layout = models.ForeignKey(SeatLayout, on_delete=models.RESTRICT, related_name="trips")
    
    departure_time = models.DateTimeField(help_text="Scheduled departure from origin.")
    arrival_time = models.DateTimeField(help_text="Scheduled arrival at destination.")
    
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.DRAFT)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return f"{self.route.name} | {self.departure_time.strftime('%Y-%m-%d %H:%M')} ({self.status})"


class TripStop(models.Model):
    """
    The specific arrival/departure times for a stop on a particular trip.
    Allows real-time delay tracking separate from the idealized RouteStop schedule.
    """

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="trip_stops")
    route_stop = models.ForeignKey(RouteStop, on_delete=models.CASCADE, related_name="trip_instances")
    
    expected_arrival = models.DateTimeField()
    expected_departure = models.DateTimeField()
    
    actual_arrival = models.DateTimeField(null=True, blank=True)
    actual_departure = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["expected_arrival"]
        constraints = [
            models.UniqueConstraint(fields=["trip", "route_stop"], name="unique_stop_per_trip")
        ]

    def __str__(self) -> str:
        return f"{self.trip.id} - {self.route_stop.stop.name}"


class FareRule(models.Model):
    """
    Dynamic pricing rules for a trip. 
    E.g., Seater = ₹500, Sleeper Lower = ₹800, Sleeper Upper = ₹750.
    """

    trip = models.ForeignKey(Trip, on_delete=models.CASCADE, related_name="fare_rules")
    seat_type = models.CharField(max_length=20, choices=Seat.SeatType.choices)
    deck = models.CharField(
        max_length=20, 
        choices=Seat.Deck.choices, 
        null=True, 
        blank=True, 
        help_text="Leave blank if fare applies to both decks."
    )
    price = models.DecimalField(max_digits=8, decimal_places=2, help_text="Base fare in INR.")

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=["trip", "seat_type", "deck"], 
                name="unique_fare_per_seat_type_and_deck"
            )
        ]

    def __str__(self) -> str:
        deck_info = f" ({self.deck})" if self.deck else ""
        return f"₹{self.price} for {self.seat_type}{deck_info} on Trip {self.trip.id}"