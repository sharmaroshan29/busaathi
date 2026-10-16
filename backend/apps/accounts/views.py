from django.db import DatabaseError, connection
from django.http import JsonResponse


def health_check(request):
    try:
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1;")
            cursor.fetchone()

        return JsonResponse(
            {"status": "ok", "database": "connected"},
            status=200,
        )
    except DatabaseError:
        return JsonResponse(
            {"status": "error", "database": "disconnected"},
            status=503,
        )