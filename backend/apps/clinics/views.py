from datetime import timedelta

from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics

from .models import Clinic, Doctor, Specialty, TimeSlot
from .serializers import ClinicSerializer, DoctorSerializer, SpecialtySerializer, TimeSlotSerializer


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
