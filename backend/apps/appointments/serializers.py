from django.utils import timezone
from rest_framework import serializers

from apps.clinics.models import TimeSlot
from apps.intake.models import Intake

from .models import Appointment, Patient
from .queue import get_queue_info, next_queue_number


class PatientInputSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=200)
    phone = serializers.CharField(max_length=20)

    def validate_phone(self, value):
        phone = value.replace(" ", "").replace("-", "")
        if phone.startswith("8"):
            phone = "+7" + phone[1:]
        if len(phone) != 12 or not phone.startswith("+7") or not phone[1:].isdigit():
            raise serializers.ValidationError("Enter a phone like +77011234567.")
        return phone


class BookingSerializer(serializers.Serializer):
    intake_id = serializers.IntegerField()
    slot_id = serializers.IntegerField()
    specialty_code = serializers.CharField(required=False)
    patient = PatientInputSerializer()

    def validate(self, data):
        intake = Intake.objects.filter(id=data["intake_id"]).first()
        if intake is None:
            raise serializers.ValidationError({"intake_id": "Intake not found."})
        if Appointment.objects.filter(intake=intake).exists():
            raise serializers.ValidationError({"intake_id": "This intake is already used."})

        slot = TimeSlot.objects.filter(id=data["slot_id"]).first()
        if slot is None:
            raise serializers.ValidationError({"slot_id": "Slot not found."})
        if slot.is_booked:
            raise serializers.ValidationError({"slot_id": "This slot is already booked."})
        if slot.start < timezone.now():
            raise serializers.ValidationError({"slot_id": "This slot is in the past."})

        code = data.get("specialty_code") or intake.specialty.code
        if slot.doctor.clinic != intake.clinic or slot.doctor.specialty.code != code:
            raise serializers.ValidationError({"slot_id": "This slot is for another specialist."})

        data["intake"] = intake
        data["slot"] = slot
        return data

    def create(self, data):
        patient, created = Patient.objects.get_or_create(
            phone=data["patient"]["phone"],
            defaults={"full_name": data["patient"]["full_name"]},
        )
        slot = data["slot"]

        appointment = Appointment.objects.create(
            patient=patient,
            doctor=slot.doctor,
            slot=slot,
            intake=data["intake"],
            urgency=data["intake"].urgency,
            queue_number=next_queue_number(slot.doctor, slot.start),
        )

        slot.is_booked = True
        slot.save()
        return appointment


class QueueInfoSerializer(serializers.Serializer):
    position = serializers.IntegerField(allow_null=True)
    people_ahead = serializers.IntegerField()
    wait_minutes = serializers.IntegerField(allow_null=True)


class AppointmentSerializer(serializers.ModelSerializer):
    clinic = serializers.CharField(source="doctor.clinic.name")
    doctor = serializers.CharField(source="doctor.full_name")
    room = serializers.CharField(source="doctor.room")
    specialty = serializers.CharField(source="doctor.specialty.name")
    slot_start = serializers.DateTimeField(source="slot.start")
    first_name = serializers.SerializerMethodField()
    queue = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "token",
            "status",
            "queue_number",
            "urgency",
            "urgency_confirmed",
            "clinic",
            "doctor",
            "room",
            "specialty",
            "slot_start",
            "first_name",
            "queue",
        ]

    def get_first_name(self, appointment) -> str:
        return appointment.patient.full_name.split()[0]

    def get_queue(self, appointment) -> QueueInfoSerializer:
        return get_queue_info(appointment)


class StaffAppointmentSerializer(AppointmentSerializer):
    patient_name = serializers.CharField(source="patient.full_name")
    patient_phone = serializers.CharField(source="patient.phone")
    reasons = serializers.JSONField(source="intake.reasons", default=list)

    class Meta(AppointmentSerializer.Meta):
        fields = ["id", "patient_name", "patient_phone", "reasons"] + AppointmentSerializer.Meta.fields


class StaffUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["urgency", "urgency_confirmed", "status"]
