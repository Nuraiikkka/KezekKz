from datetime import datetime

from django.db import transaction
from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.types import OpenApiTypes
from drf_spectacular.utils import OpenApiParameter, extend_schema, extend_schema_view, inline_serializer
from rest_framework import generics, permissions, serializers, status
from rest_framework.exceptions import ValidationError
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clinics.models import Doctor, TimeSlot

from . import queue
from .models import Appointment
from .serializers import (
    AppointmentCreateSerializer,
    AppointmentStatusSerializer,
    StaffAppointmentSerializer,
    StaffAppointmentUpdateSerializer,
)

APPOINTMENT_RELATED = ["clinic", "doctor", "specialty", "slot", "patient", "intake"]


class AppointmentCreateView(APIView):
    authentication_classes = []

    @extend_schema(
        tags=["Appointments"],
        summary="Book a slot",
        description=(
            "Books a free slot using a submitted intake. `specialty_code` is optional (defaults to the "
            "suggestion). Returns the `tracking_token` the patient uses to follow the queue."
        ),
        request=AppointmentCreateSerializer,
        responses={201: AppointmentStatusSerializer},
    )
    def post(self, request):
        serializer = AppointmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        return Response(AppointmentStatusSerializer(appointment).data, status=status.HTTP_201_CREATED)


@extend_schema_view(
    get=extend_schema(
        tags=["Appointments"],
        summary="Track live queue status",
        description="Public live status by tracking token (queue position, estimated wait).",
    )
)
class AppointmentTrackView(generics.RetrieveAPIView):
    """Public live status by tracking token (UC-2). The token is the only credential."""

    authentication_classes = []

    serializer_class = AppointmentStatusSerializer
    lookup_field = "tracking_token"
    lookup_url_kwarg = "token"
    queryset = Appointment.objects.select_related(*APPOINTMENT_RELATED)


class AppointmentCancelView(APIView):
    authentication_classes = []

    @extend_schema(
        tags=["Appointments"],
        summary="Cancel appointment",
        description="Only while status is `booked`. Frees the slot.",
        request=None,
        responses=AppointmentStatusSerializer,
    )
    def post(self, request, token):
        with transaction.atomic():
            appointment = get_object_or_404(Appointment.objects.select_for_update(), tracking_token=token)
            if appointment.status != Appointment.Status.BOOKED:
                raise ValidationError({"status": "Only booked (not yet checked-in) appointments can be cancelled."})
            appointment.status = Appointment.Status.CANCELLED
            appointment.save(update_fields=["status", "updated_at"])
            TimeSlot.objects.filter(pk=appointment.slot_id).update(is_booked=False)
        return Response(AppointmentStatusSerializer(appointment).data)


# --- Staff ------------------------------------------------------------------


class IsClinicStaff(permissions.BasePermission):
    def has_permission(self, request, view):
        return bool(request.user and request.user.is_authenticated and request.user.is_staff)


class StaffQueueView(APIView):
    """
    Live queue of one doctor for one day, in serving order.

    Query params: doctor (id, required), date (YYYY-MM-DD, default today).
    """

    permission_classes = [IsClinicStaff]

    @extend_schema(
        tags=["Staff"],
        summary="Doctor's live queue for a day",
        parameters=[
            OpenApiParameter("doctor", OpenApiTypes.INT, required=True, description="Doctor id"),
            OpenApiParameter("date", OpenApiTypes.DATE, description="YYYY-MM-DD, default today"),
        ],
        responses=inline_serializer(
            "StaffQueue",
            fields={
                "doctor": inline_serializer(
                    "StaffQueueDoctor",
                    fields={
                        "id": serializers.IntegerField(),
                        "full_name": serializers.CharField(),
                        "room": serializers.CharField(),
                    },
                ),
                "date": serializers.DateField(),
                "current_delay_minutes": serializers.IntegerField(),
                "appointments": StaffAppointmentSerializer(many=True),
            },
        ),
    )
    def get(self, request):
        doctor_id = request.query_params.get("doctor")
        if not doctor_id:
            raise ValidationError({"doctor": "This query parameter is required."})
        doctor = get_object_or_404(Doctor.objects.select_related("specialty"), pk=doctor_id)

        date_str = request.query_params.get("date")
        if date_str:
            try:
                day = datetime.strptime(date_str, "%Y-%m-%d").date()
            except ValueError:
                raise ValidationError({"date": "Use YYYY-MM-DD format."})
        else:
            day = timezone.localdate()

        items = queue.ordered_queue(doctor, day)
        for item in items:
            item.doctor = doctor
        data = StaffAppointmentSerializer(items, many=True, context={"queue": items}).data
        return Response(
            {
                "doctor": {"id": doctor.id, "full_name": doctor.full_name, "room": doctor.room},
                "date": day,
                "current_delay_minutes": doctor.current_delay_minutes,
                "appointments": data,
            }
        )


@extend_schema_view(
    patch=extend_schema(
        tags=["Staff"],
        summary="Confirm urgency / change status",
        description=(
            "Setting `urgency` marks it confirmed. Status transitions: booked → checked_in | no_show | cancelled, "
            "checked_in → in_progress | cancelled, in_progress → completed."
        ),
        responses=StaffAppointmentSerializer,
    )
)
class StaffAppointmentUpdateView(generics.UpdateAPIView):
    permission_classes = [IsClinicStaff]
    serializer_class = StaffAppointmentUpdateSerializer
    queryset = Appointment.objects.select_related(*APPOINTMENT_RELATED)
    http_method_names = ["patch"]

    def update(self, request, *args, **kwargs):
        super().update(request, *args, **kwargs)
        appointment = self.get_queryset().get(pk=kwargs["pk"])
        return Response(StaffAppointmentSerializer(appointment).data)
