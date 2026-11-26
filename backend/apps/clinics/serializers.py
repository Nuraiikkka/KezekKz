from rest_framework import serializers

from .models import Clinic, Doctor, Specialty, TimeSlot


class ClinicSerializer(serializers.ModelSerializer):
    class Meta:
        model = Clinic
        fields = ["id", "name", "slug", "address", "phone", "hours", "map_url"]


class SpecialtySerializer(serializers.ModelSerializer):
    class Meta:
        model = Specialty
        fields = ["id", "code", "name", "visit_minutes", "price"]


class DoctorSerializer(serializers.ModelSerializer):
    specialty = serializers.CharField(source="specialty.name")

    class Meta:
        model = Doctor
        fields = ["id", "full_name", "room", "specialty", "delay_minutes"]


class DoctorDelaySerializer(serializers.ModelSerializer):
    delay_minutes = serializers.IntegerField(min_value=0, max_value=240)

    class Meta:
        model = Doctor
        fields = ["delay_minutes"]


class TimeSlotSerializer(serializers.ModelSerializer):
    doctor = serializers.CharField(source="doctor.full_name")

    class Meta:
        model = TimeSlot
        fields = ["id", "doctor", "start", "end"]
