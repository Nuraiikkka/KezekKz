from rest_framework import serializers

from .models import Clinic, Doctor, Specialty, TimeSlot


class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = ["id", "name", "slug", "address", "phone"]


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ["id", "code", "name", "avg_consultation_minutes"]


class DoctorSerializer(serializers.ModelSerializer):
    specialty = SpecialtySerializer(read_only=True)

    class Meta:
        model = Doctor
        fields = ["id", "full_name", "room", "specialty", "current_delay_minutes"]


class TimeSlotSerializer(serializers.ModelSerializer):
    doctor_id = serializers.IntegerField(source="doctor.id", read_only=True)
    doctor_name = serializers.CharField(source="doctor.full_name", read_only=True)

    class Meta:
        model = TimeSlot
        fields = ["id", "doctor_id", "doctor_name", "start", "end"]
