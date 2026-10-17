from rest_framework import generics
from rest_framework.permissions import AllowAny
from django.utils.dateparse import parse_date
from .models import Trip
from .serializers import TripSearchSerializer
from django.db.models import Count, Q
from django.utils import timezone

# Create your views here.

class TripSearchAPIView(generics.ListAPIView):
    """
    GET /api/v1/trips/search/?origin=PRY&destination=LKO&date=2026-10-25
    Searches available bus trips based on origin, destination, and date (PRD Phase 4, Task 1).
    """
    serializer_class = TripSearchSerializer
    permission_classes = [AllowAny]  # Anyone can search without logging in!

    def get_queryset(self):
        now =timezone.now()
        # 1. STRICT PRD RULE: Only return PUBLISHED trips that haven't departed yet
        
        queryset = Trip.objects.filter(
            status=Trip.Status.PUBLISHED,
            departure_time__gt=timezone.now()
        ).annotate(
            # Count how many seats are permanently confirmed
            booked_seats_count=Count(
                'bookings__seats',
                filter=Q(bookings__status='confirmed'),
                distinct=True
            ),
            # Count how many seats are temporarily locked by other users right now
            held_seats_count=Count(
                'seat_holds',
                filter=Q(seat_holds__expires_at__gt=now),
                distinct=True
            )
        )

        # 2. Grab search parameters from the URL (e.g., ?origin=PRY)
        origin_code = self.request.query_params.get("origin")
        dest_code = self.request.query_params.get("destination")
        travel_date = self.request.query_params.get("date")

        # 3. Apply filters dynamically
        if origin_code:
            queryset = queryset.filter(route__origin__code__iexact=origin_code)
        if dest_code:
            queryset = queryset.filter(route__destination__code__iexact=dest_code)
        if travel_date:
            parsed_date = parse_date(travel_date)
            if parsed_date:
                # Filter trips where the departure_time falls on this specific date
                queryset = queryset.filter(departure_time__date=parsed_date)

        # 4. Database Optimization: Use select_related to prevent N+1 query problems
        return queryset.select_related("route__origin", "route__destination", "operator", "bus", "seat_layout")


