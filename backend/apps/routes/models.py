from django.db import models


class City(models.Model):
    """Represents a city where BuSaathi operates (e.g., Prayagraj, Lucknow)."""

    name = models.CharField(max_length=100, unique=True)
    state = models.CharField(max_length=100)
    code = models.CharField(max_length=10, unique=True, help_text="Short code, e.g., 'IXD' or 'PRY'")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name}, {self.state}"


class Stop(models.Model):
    """Specific physical boarding/dropping location within a city."""

    city = models.ForeignKey(City, on_delete=models.CASCADE, related_name="stops")
    name = models.CharField(max_length=150, help_text="e.g., Civil Lines Bus Stand")
    address = models.TextField()
    latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return f"{self.name} ({self.city.name})"


class Route(models.Model):
    """Defines a mainline route between an origin city and a destination city."""

    origin = models.ForeignKey(City, on_delete=models.CASCADE, related_name="routes_origin")
    destination = models.ForeignKey(City, on_delete=models.CASCADE, related_name="routes_destination")
    name = models.CharField(max_length=200, help_text="e.g., Prayagraj to Varanasi Express Route")
    distance_km = models.PositiveIntegerField(help_text="Approximate distance in kilometers.")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self) -> str:
        return self.name


class RouteStop(models.Model):
    """
    Ordered intermediate or terminal stops along a route (PRD Phase 3, Task 4).
    'stop_order' ensures we know the exact sequence (1st stop, 2nd stop, etc.).
    """

    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name="route_stops")
    stop = models.ForeignKey(Stop, on_delete=models.CASCADE, related_name="route_associations")
    stop_order = models.PositiveIntegerField(help_text="Sequence order: 1 for origin, 2 for first stop, etc.")
    arrival_offset_minutes = models.PositiveIntegerField(
        help_text="Minutes from trip departure time when bus reaches this stop."
    )

    class Meta:
        ordering = ["stop_order"]
        constraints = [
            models.UniqueConstraint(
                fields=["route", "stop_order"],
                name="unique_route_stop_order",
            )
        ]

    def __str__(self) -> str:
        return f"{self.route.name} [Stop {self.stop_order}: {self.stop.name}]"