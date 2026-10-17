from django.core.management.base import BaseCommand
from apps.bookings.services import release_expired_holds


class Command(BaseCommand):
    help = "Releases all expired seat holds in the database."

    def handle(self, *args, **options):
        self.stdout.write("Checking for expired seat holds...")
        
        released_count = release_expired_holds()
        
        if released_count > 0:
            self.stdout.write(self.style.SUCCESS(f"Successfully released {released_count} expired hold(s)."))
        else:
            self.stdout.write(self.style.WARNING("No expired holds found. Database is clean."))