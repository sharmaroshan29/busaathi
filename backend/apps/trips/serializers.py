from rest_framework import serializers
from .models import Trip

class TripSearchSerializer(serializers.ModelSerializer):
    """Formats the Trip data for the passenger search results."""
    
    # We pull friendly names across the foreign keys so the frontend doesn't just get raw IDs
    origin_city = serializers.CharField(source='route.origin.name', read_only=True)
    destination_city = serializers.CharField(source='route.destination.name', read_only=True)
    operator_name = serializers.CharField(source='operator.name', read_only=True)
    bus_type = serializers.CharField(source='bus.get_bus_type_display', read_only=True)

    available_seats =serializers.SerializerMethodField()

    class Meta:
        model = Trip
        fields = (
            "id",
            "operator_name",
            "origin_city",
            "destination_city",
            "departure_time",
            "arrival_time",
            "bus_type",
            "available_seats"
        )
    def get_available_seats(self, obj) -> int:
        """
        Calculates availability using the annotated counts from the view's queryset.
        Total Capacity - (Confirmed Seats + Temporarily Held Seats).
        """
        total = obj.seat_layout.total_capacity
        
        # getattr is used with a default of 0 in case the serializer is called 
        # from somewhere else that didn't run the .annotate() query
        booked = getattr(obj, 'booked_seats_count', 0)
        held = getattr(obj, 'held_seats_count', 0)
        
        return max(0, total - booked - held)