from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from apps.operators.models import Operator, OperatorPaymentProfile
from apps.fleet.models import Bus, SeatLayout, Seat
from apps.routes.models import City, Stop, Route, RouteStop
from apps.trips.models import Trip, TripStop, FareRule


class Command(BaseCommand):
    help = "Seeds the database with exact schema-matched test data for BuSaathi."

    def handle(self, *args, **kwargs):
        self.stdout.write("Seeding BuSaathi database...")
        now = timezone.now()

 # 1. Create Operator & Payment Profile
        operator, _ = Operator.objects.get_or_create(
            name="Zingbus Travels",  # <-- Look up by name (which already exists!)
            defaults={
                "slug": "zingbus-travels",
                "contact_email": "support@zingbus.com",
                "contact_phone": "9876543210",
                "status": "active",
                "merchant_id": "mock_merch_zingbus_01",
            }
        )
        OperatorPaymentProfile.objects.get_or_create(
            operator=operator,
            defaults={
                "gateway_account_id": "acct_mock_zingbus_01",
                "payout_status": "enabled",
                "bank_details_verified": True,
            }
        )
        self.stdout.write(self.style.SUCCESS(f"1. Operator ready: {operator.name}"))

        # 2. Create Bus, SeatLayout & 10 Seats
        bus, _ = Bus.objects.get_or_create(
            registration_number="UP-70-AB-1234",
            defaults={
                "operator": operator,
                "bus_type": "AC Sleeper (2+1)",
                "make_and_model": "Volvo 9600",
                "is_active": True,
            }
        )
        layout, _ = SeatLayout.objects.get_or_create(
            bus=bus,
            version=1,
            defaults={
                "effective_from": now - timedelta(days=30),
                "total_capacity": 10,
                "is_active": True,
            }
        )
        for i in range(1, 11):
            is_lower = i <= 5
            Seat.objects.get_or_create(
                layout=layout,
                seat_number=f"L{i}" if is_lower else f"U{i-5}",
                defaults={
                    "seat_type": "sleeper" if is_lower else "semi_sleeper",
                    "deck": "lower" if is_lower else "upper",
                    "grid_row": (i - 1) % 5 + 1,
                    "grid_col": 1 if is_lower else 2,
                    "is_window": (i % 2 == 1),
                    "is_women_only": (i == 1),
                }
            )
        self.stdout.write(self.style.SUCCESS(f"2. Bus & SeatLayout ready: {bus.registration_number} ({layout.seats.count()} seats)"))

        # 3. Create Cities & Stops
        pry, _ = City.objects.get_or_create(
            code="PRY",
            defaults={"name": "Prayagraj", "state": "Uttar Pradesh", "is_active": True}
        )
        rbl, _ = City.objects.get_or_create(
            code="RBL",
            defaults={"name": "Raebareli", "state": "Uttar Pradesh", "is_active": True}
        )
        lko, _ = City.objects.get_or_create(
            code="LKO",
            defaults={"name": "Lucknow", "state": "Uttar Pradesh", "is_active": True}
        )

        stop_pry, _ = Stop.objects.get_or_create(
            city=pry, name="Prayagraj Civil Lines",
            defaults={"address": "MG Marg, Civil Lines", "latitude": Decimal("25.450000"), "longitude": Decimal("81.830000"), "is_active": True}
        )
        stop_rbl, _ = Stop.objects.get_or_create(
            city=rbl, name="Raebareli Bypass",
            defaults={"address": "NH-30 Bypass", "latitude": Decimal("26.210000"), "longitude": Decimal("81.240000"), "is_active": True}
        )
        stop_lko, _ = Stop.objects.get_or_create(
            city=lko, name="Lucknow Alambagh ISBT",
            defaults={"address": "Alambagh Bus Stand", "latitude": Decimal("26.810000"), "longitude": Decimal("80.900000"), "is_active": True}
        )

        # 4. Create Route & RouteStops
        route, _ = Route.objects.get_or_create(
            origin=pry,
            destination=lko,
            name="Prayagraj - Lucknow Express",
            defaults={"distance_km": 200, "is_active": True}
        )
        rs1, _ = RouteStop.objects.get_or_create(route=route, stop=stop_pry, defaults={"stop_order": 1, "arrival_offset_minutes": 0})
        rs2, _ = RouteStop.objects.get_or_create(route=route, stop=stop_rbl, defaults={"stop_order": 2, "arrival_offset_minutes": 120})
        rs3, _ = RouteStop.objects.get_or_create(route=route, stop=stop_lko, defaults={"stop_order": 3, "arrival_offset_minutes": 240})
        self.stdout.write(self.style.SUCCESS(f"3. Route ready: {route.name}"))

        # 5. Create Active Trip for Tomorrow + TripStops + FareRules
        tomorrow = (now + timedelta(days=1)).replace(hour=8, minute=0, second=0, microsecond=0)
        arrival = tomorrow + timedelta(hours=4)

        trip, _ = Trip.objects.get_or_create(
            operator=operator,
            route=route,
            bus=bus,
            departure_time=tomorrow,
            defaults={
                "seat_layout": layout,
                "arrival_time": arrival,
                "status": "published",
            }
        )

        for rs in [rs1, rs2, rs3]:
            arr_time = tomorrow + timedelta(minutes=rs.arrival_offset_minutes)
            TripStop.objects.get_or_create(
                trip=trip,
                route_stop=rs,
                defaults={
                    "expected_arrival": arr_time,
                    "expected_departure": arr_time + timedelta(minutes=10),
                }
            )

        FareRule.objects.get_or_create(
            trip=trip, seat_type="sleeper", deck="lower",
            defaults={"price": Decimal("699.00")}
        )
        FareRule.objects.get_or_create(
            trip=trip, seat_type="semi_sleeper", deck="upper",
            defaults={"price": Decimal("499.00")}
        )

        self.stdout.write(self.style.SUCCESS(
            f"4. Trip ready! Trip ID: {trip.id} | Boarding TripStop ID: {TripStop.objects.filter(trip=trip).first().id} | Drop TripStop ID: {TripStop.objects.filter(trip=trip).last().id}"
        ))
        self.stdout.write(self.style.SUCCESS("Database seeding completed 100% successfully!"))