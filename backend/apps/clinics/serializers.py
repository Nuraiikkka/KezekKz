from rest_framework import serializers

from .models import Clinic, Doctor, Specialty, TimeSlot


class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = ["id", "name", "slug", "address"]


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ["id", "code", "name", "visit_minutes"]


class DoctorSerializer(serializers.ModelSerializer):
    specialty = serializers.CharField(source="specialty.name")

    class Meta:
        model = Doctor
        fields = ["id", "full_name", "room", "specialty", "delay_minutes"]


class TimeSlotSerializer(serializers.ModelSerializer):
    doctor = serializers.CharField(source="doctor.full_name")

    class Meta:
        model = TimeSlot
        fields = ["id", "doctor", "start", "end"]
