from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status, generics
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError
from .models import Booking, BookingSeat

from .serializers import SeatHoldRequestSerializer, CheckoutRequestSerializer, PaymentRequestSerializer, BoardingManifestSerializer
from .services import hold_seats_for_checkout, create_booking_from_hold, process_mock_payment, cancel_booking


class CreateSeatHoldAPIView(APIView):
    """
    POST /api/v1/bookings/hold/
    Temporarily locks seats for the authenticated user.
    """
    
    # Only logged-in users can lock seats
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = SeatHoldRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            # Call the atomic service layer we just wrote
            holds = hold_seats_for_checkout(
                user=request.user,
                trip_id=serializer.validated_data["trip_id"],
                seat_ids=serializer.validated_data["seat_ids"],
            )
            return Response(
                {"message": f"Successfully locked {len(holds)} seat(s) for 10 minutes."},
                status=status.HTTP_201_CREATED
            )
        # Catch our custom business logic errors (e.g., "Seat already booked")
        except ValidationError as e:
            return Response(
                {"error": e.message if hasattr(e, 'message') else str(e)}, 
                status=status.HTTP_400_BAD_REQUEST
            )
class CheckoutAPIView(APIView):
    """POST /api/v1/bookings/checkout"""

    permission_classes =[IsAuthenticated]

    def post(self, request):
        serializer =CheckoutRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            booking = create_booking_from_hold(
                user=request.user,
                trip_id=serializer.validated_data["trip_id"],
                seat_ids=serializer.validated_data["seat_ids"],
                boarding_stop_id=serializer.validated_data["boarding_stop_id"],
                drop_stop_id=serializer.validated_data["drop_stop_id"],
            )
            return Response(
                {
                    "message": "Booking created successfully",
                    "pnr": booking.pnr,
                    "total_fare": str(booking.total_fare),
                    "booking_id": booking.id
                },
                status=status.HTTP_201_CREATED
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class PaymentAPIView(APIView):
    """POST/api/v1/bookings/pay/"""

    permission_classes =[IsAuthenticated]

    def post(self, request):
        serializer = PaymentRequestSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        try:
            payment_txn = process_mock_payment(
                booking_id=serializer.validated_data["booking_id"],
                idempotency_key=serializer.validated_data["idempotency_key"],
                outcome=serializer.validated_data["outcome"]
            )
            return Response(
                {
                    "message": f"Payment transaction processed with status: {payment_txn.status}",
                    "order_id": str(payment_txn.provider_order_id),
                    "status": payment_txn.status
                },
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)

class CancelBookingAPIView(APIView):
    """POST/api/v1/bookings/<booking_id>/cancel/
    cancel the booking and calculate the applicable refund"""

    permission_classes =[IsAuthenticated]

    def post(self, request, booking_id):
        try:
            booking =cancel_booking(user=request.user, booking_id=booking_id)
            refund_amount =booking.refund.amount if hasattr(booking, 'refund') else "0.00"

            return Response(
                {
                    "message": "Booking Cancelled Successfully",
                    "pnr": booking.pnr,
                    "refund_amount": refund_amount
                },
                status=status.HTTP_200_OK
            )
        except ValidationError as e:
            return Response({"error": str(e)}, status=status.HTTP_400_BAD_REQUEST)
        except Booking.DoesNotExist:
            return Response({"error": "Booking not found."}, status=status.HTTP_404_NOT_FOUND)


class TripManifestAPIView(generics.ListAPIView):
    """
    GET /api/v1/bookings/trip/<trip_id>/manifest/
    Returns a list of all confirmed passengers for a specific trip.
    """
    serializer_class = BoardingManifestSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        trip_id = self.kwargs['trip_id']
        
        # We only want to show passengers whose bookings are fully CONFIRMED.
        # select_related optimizes the database query to prevent N+1 lookups.
        return BookingSeat.objects.filter(
            booking__trip_id=trip_id,
            booking__status=Booking.Status.CONFIRMED
        ).select_related(
            'booking', 
            'seat', 
            'booking__boarding_stop__route_stop__stop', 
            'booking__drop_stop__route_stop__stop'
        ).order_by('seat__seat_number')