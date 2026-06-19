from django.urls import path
from . import views

urlpatterns = [
    path("health/", views.health),
    path("trips/", views.create_trip),
    path("trips/<int:trip_id>/", views.get_trip),
    path("trips/<int:trip_id>/logs/", views.get_trip_logs),
    path("trips/<int:trip_id>/pdf/", views.download_trip_pdf),
]
