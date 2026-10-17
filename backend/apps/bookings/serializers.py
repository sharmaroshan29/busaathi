from rest_framework import serializers


class SeatHoldRequestSerializer(serializers.Serializer):
    """Validates the incoming payload when a user clicks 'Proceed to Checkout'."""
    
    trip_id = serializers.IntegerField()
    # Expects a list of seat IDs, e.g., [15, 16]
    seat_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of seat IDs to lock."
    )