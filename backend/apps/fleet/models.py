from django.db import models
from apps.operators.models import Operator


class Bus(models.Model):
    """Represents a physical vehicle owned by an operator."""

    class BusType(models.TextChoices):
        AC_SEATER = "ac_seater", "AC Seater"
        NON_AC_SEATER = "non_ac_seater", "Non-AC Seater"
        AC_SLEEPER = "ac_sleeper", "AC Sleeper"
        NON_AC_SLEEPER = "non_ac_sleeper", "Non-AC Sleeper"
        AC_SEATER_SLEEPER = "ac_seater_sleeper", "AC Seater/Sleeper (2+1)"
        VOLVO_MULTI_AXLE = "volvo_multi_axle", "Volvo Multi-Axle AC"

    operator = models.ForeignKey(Operator, on_delete=models.CASCADE, related_name="buses")
    registration_number = models.CharField(max_length=20, unique=True, help_text="e.g., UP70 AB 1234")
    bus_type = models.CharField(max_length=30, choices=BusType.choices)
    make_and_model = models.CharField(max_length=100, blank=True, help_text="e.g., Ashok Leyland, Volvo B11R")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.registration_number} ({self.get_bus_type_display()})"


class SeatLayout(models.Model):
    """
    A versioned seating blueprint for a bus. 
    If a bus is remodeled, a new version is created so past trips retain the old layout.
    """
    
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name="layouts")
    version = models.PositiveIntegerField(default=1)
    effective_from = models.DateTimeField(auto_now_add=True)
    total_capacity = models.PositiveIntegerField()
    is_active = models.BooleanField(default=True, help_text="Only one layout should be active per bus at a time.")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["bus", "version"], name="unique_bus_layout_version")
        ]

    def __str__(self) -> str:
        return f"Layout v{self.version} for {self.bus.registration_number}"


class Seat(models.Model):
    """Individual seat or sleeper berth mapping on the layout grid."""

    class SeatType(models.TextChoices):
        SEATER = "seater", "Seater"
        SLEEPER = "sleeper", "Sleeper Berth"
        SEMI_SLEEPER = "semi_sleeper", "Semi-Sleeper"

    class Deck(models.TextChoices):
        LOWER = "lower", "Lower Deck"
        UPPER = "upper", "Upper Deck"

    layout = models.ForeignKey(SeatLayout, on_delete=models.CASCADE, related_name="seats")
    seat_number = models.CharField(max_length=10, help_text="e.g., L1, U12, 4A")
    seat_type = models.CharField(max_length=20, choices=SeatType.choices, default=SeatType.SEATER)
    deck = models.CharField(max_length=20, choices=Deck.choices, default=Deck.LOWER)
    
    # Frontend rendering coordinates
    grid_row = models.PositiveIntegerField(help_text="Row position on the visual grid.")
    grid_col = models.PositiveIntegerField(help_text="Column position on the visual grid.")
    
    is_window = models.BooleanField(default=False)
    is_women_only = models.BooleanField(default=False, help_text="Reserved for female passengers.")

    class Meta:
        constraints = [
            models.UniqueConstraint(fields=["layout", "seat_number"], name="unique_seat_number_per_layout")
        ]

    def __str__(self) -> str:
        return f"Seat {self.seat_number} ({self.deck}, {self.seat_type})"