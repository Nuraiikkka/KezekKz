from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from drf_spectacular.utils import extend_schema
from rest_framework import generics
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.appointments.notify import notify_delay, notify_queue
from apps.appointments.waitlist import expire_offers

from .models import Clinic, Doctor, Specialty, TimeSlot
from .serializers import (
    ClinicSerializer,
    DoctorDelaySerializer,
    DoctorSerializer,
    SpecialtySerializer,
    TimeSlotSerializer,
)


class ClinicListView(generics.ListAPIView):
    queryset = Clinic.objects.all()
    serializer_class = ClinicSerializer


class SpecialtyListView(generics.ListAPIView):
    serializer_class = SpecialtySerializer

    def get_queryset(self):
        clinic = get_object_or_404(Clinic, slug=self.kwargs["slug"])
        return Specialty.objects.filter(clinic=clinic)


class DoctorListView(generics.ListAPIView):
    serializer_class = DoctorSerializer

    def get_queryset(self):
        clinic = get_object_or_404(Clinic, slug=self.kwargs["slug"])
        return Doctor.objects.filter(clinic=clinic)


class SlotListView(generics.ListAPIView):
    serializer_class = TimeSlotSerializer

    def get_queryset(self):
        expire_offers()
        clinic = get_object_or_404(Clinic, slug=self.kwargs["slug"])
        now = timezone.now()
        slots = TimeSlot.objects.filter(
            doctor__clinic=clinic,
            is_booked=False,
            start__gt=now,
            start__lt=now + timedelta(days=7),
        )
        specialty = self.request.query_params.get("specialty")
        if specialty:
            slots = slots.filter(doctor__specialty__code=specialty)
        return slots


class DoctorDelayView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=DoctorDelaySerializer, responses=DoctorSerializer)
    def patch(self, request, pk):
        doctor = get_object_or_404(Doctor, id=pk)
        serializer = DoctorDelaySerializer(doctor, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        notify_delay(doctor)
        notify_queue(doctor)
        return Response(DoctorSerializer(doctor).data)
