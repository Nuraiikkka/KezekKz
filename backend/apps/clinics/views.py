from datetime import datetime, time, timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view
from rest_framework import generics
from rest_framework.exceptions import ValidationError

from .models import Clinic, Doctor, Specialty, TimeSlot
from .serializers import ClinicSerializer, DoctorSerializer, SpecialtySerializer, TimeSlotSerializer


@extend_schema_view(get=extend_schema(tags=["Clinics"], summary="List clinics"))
class ClinicListView(generics.ListAPIView):
    authentication_classes = []

    serializer_class = ClinicSerializer
    queryset = Clinic.objects.filter(is_active=True)


@extend_schema_view(get=extend_schema(tags=["Clinics"], summary="Clinic details"))
class ClinicDetailView(generics.RetrieveAPIView):
    authentication_classes = []

    serializer_class = ClinicSerializer
    queryset = Clinic.objects.filter(is_active=True)
    lookup_field = "slug"


@extend_schema_view(get=extend_schema(tags=["Clinics"], summary="Clinic specialties"))
class SpecialtyListView(generics.ListAPIView):
    authentication_classes = []

    serializer_class = SpecialtySerializer

    def get_queryset(self):
        clinic = get_object_or_404(Clinic, slug=self.kwargs["slug"], is_active=True)
        return Specialty.objects.filter(clinic=clinic)


@extend_schema_view(
    get=extend_schema(
        tags=["Clinics"],
        summary="Clinic doctors",
        parameters=[OpenApiParameter("specialty", OpenApiTypes.STR, description="Specialty code")],
    )
)
class DoctorListView(generics.ListAPIView):
    authentication_classes = []

    serializer_class = DoctorSerializer

    def get_queryset(self):
        clinic = get_object_or_404(Clinic, slug=self.kwargs["slug"], is_active=True)
        qs = Doctor.objects.filter(clinic=clinic, is_active=True).select_related("specialty")
        specialty = self.request.query_params.get("specialty")
        if specialty:
            qs = qs.filter(specialty__code=specialty)
        return qs


@extend_schema_view(
    get=extend_schema(
        tags=["Clinics"],
        summary="Free slots",
        parameters=[
            OpenApiParameter("specialty", OpenApiTypes.STR, required=True, description="Specialty code"),
            OpenApiParameter("date", OpenApiTypes.DATE, description="YYYY-MM-DD; default next 7 days"),
            OpenApiParameter("part_of_day", OpenApiTypes.STR, enum=["morning", "afternoon"]),
        ],
    )
)
class AvailableSlotListView(generics.ListAPIView):
    """
    Free future slots of a clinic.

    Query params:
      specialty  – specialty code (required)
      date       – YYYY-MM-DD (optional, defaults to the next 7 days)
      part_of_day – morning | afternoon (optional, matches intake question)
    """

    authentication_classes = []

    serializer_class = TimeSlotSerializer
    pagination_class = None

    def get_queryset(self):
        clinic = get_object_or_404(Clinic, slug=self.kwargs["slug"], is_active=True)
        params = self.request.query_params
        specialty = params.get("specialty")
        if not specialty:
            raise ValidationError({"specialty": "This query parameter is required."})

        now = timezone.now()
        qs = TimeSlot.objects.filter(
            doctor__clinic=clinic,
            doctor__is_active=True,
            doctor__specialty__code=specialty,
            is_booked=False,
            start__gte=now,
        ).select_related("doctor")

        date_str = params.get("date")
        if date_str:
            try:
                day = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError({"date": "Use YYYY-MM-DD format."})
            tz = timezone.get_current_timezone()
            day_start = timezone.make_aware(datetime.combine(day, time.min), tz)
            qs = qs.filter(start__gte=day_start, start__lt=day_start + timedelta(days=1))
        else:
            qs = qs.filter(start__lt=now + timedelta(days=7))

        part = params.get("part_of_day")
        if part == "morning":
            qs = qs.filter(start__hour__lt=13)
        elif part == "afternoon":
            qs = qs.filter(start__hour__gte=13)

        return qs.order_by("start")[:100]
