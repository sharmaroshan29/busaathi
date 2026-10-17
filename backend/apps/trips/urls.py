from django.urls import path
from . import views

app_name = "trips"

urlpatterns = [
    path("search/", views.TripSearchAPIView.as_view(), name="search-trips"),
]