from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from django.core.exceptions import ValidationError

from .serializers import SeatHoldRequestSerializer
from .services import hold_seats_for_checkout


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