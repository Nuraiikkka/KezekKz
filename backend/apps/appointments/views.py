from datetime import datetime

from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.clinics.models import Doctor

from .models import Appointment
from .queue import get_queue
from .serializers import AppointmentSerializer, BookingSerializer, StaffAppointmentSerializer, StaffUpdateSerializer


class AppointmentCreateView(APIView):
    @extend_schema(request=BookingSerializer, responses=AppointmentSerializer)
    def post(self, request):
        serializer = BookingSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()
        return Response(AppointmentSerializer(appointment).data, status=201)


class AppointmentDetailView(generics.RetrieveAPIView):
    queryset = Appointment.objects.all()
    serializer_class = AppointmentSerializer
    lookup_field = "token"


class AppointmentCancelView(APIView):
    @extend_schema(request=None, responses=AppointmentSerializer)
    def post(self, request, token):
        appointment = get_object_or_404(Appointment, token=token)
        if appointment.status != "booked":
            return Response({"status": ["Only booked appointments can be cancelled."]}, status=400)

        appointment.status = "cancelled"
        appointment.save()
        appointment.slot.is_booked = False
        appointment.slot.save()
        return Response(AppointmentSerializer(appointment).data)


class StaffQueueView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses=StaffAppointmentSerializer(many=True))
    def get(self, request):
        doctor = get_object_or_404(Doctor, id=request.query_params.get("doctor"))

        date = request.query_params.get("date")
        if date:
            day = datetime.strptime(date, "%Y-%m-%d").date()
        else:
            day = timezone.localdate()

        appointments = get_queue(doctor, day)
        return Response(StaffAppointmentSerializer(appointments, many=True).data)


class StaffAppointmentUpdateView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=StaffUpdateSerializer, responses=StaffAppointmentSerializer)
    def patch(self, request, pk):
        appointment = get_object_or_404(Appointment, id=pk)
        serializer = StaffUpdateSerializer(appointment, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        appointment = serializer.save()

        if "urgency" in request.data:
            appointment.urgency_confirmed = True
            appointment.save()

        if appointment.status in ["cancelled", "no_show"]:
            appointment.slot.is_booked = False
            appointment.slot.save()

        return Response(StaffAppointmentSerializer(appointment).data)
