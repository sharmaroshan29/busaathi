from rest_framework import serializers
from  .models import Booking, BookingSeat


class SeatHoldRequestSerializer(serializers.Serializer):
    """Validates the incoming payload when a user clicks 'Proceed to Checkout'."""
    
    trip_id = serializers.IntegerField()
    # Expects a list of seat IDs, e.g., [15, 16]
    seat_ids = serializers.ListField(
        child=serializers.IntegerField(),
        allow_empty=False,
        help_text="List of seat IDs to lock."
    )


class CheckoutRequestSerializer(serializers.Serializer):
    """Validate payload when converting seat holds into pending Booking"""

    trip_id =serializers.IntegerField()
    seat_ids =serializers.ListField(child=serializers.IntegerField(), allow_empty=False)
    boarding_stop_id =serializers.IntegerField()
    drop_stop_id =serializers.IntegerField()


class PaymentRequestSerializer(serializers.Serializer):
    """Validate payload when executing the mock payment gateway"""
    booking_id =serializers.IntegerField()
    idempotency_key =serializers.CharField(max_length=100)
    outcome =serializers.ChoiceField(choices=["SUCCESS", "FAILED"], default ="SUCCESS")

class BoardingManifestSerializer(serializers.ModelSerializer):
    pnr = serializers.CharField(source='booking.pnr')
    boarding_stop = serializers.CharField(source='booking.boarding_stop.route_stop.stop.name')
    drop_stop = serializers.CharField(source='booking.drop_stop.route_stop.stop.name')
    seat_number = serializers.CharField(source='seat.seat_number')

    class Meta:
        model = BookingSeat
        fields = [
            'id', 
            'pnr', 
            'passenger_name', 
            'passenger_age', 
            'passenger_gender', 
            'seat_number', 
            'boarding_stop', 
            'drop_stop'
        ]
