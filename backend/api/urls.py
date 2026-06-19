from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TripViewSet, health


router = DefaultRouter()
router.register(r"trips", TripViewSet, basename="trip")

urlpatterns = [
    path("", include(router.urls)),
    path("health/", health),
]