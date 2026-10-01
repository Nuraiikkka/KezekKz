import re

from django.db import IntegrityError, transaction
from django.utils import timezone
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from apps.clinics.models import Doctor, Specialty, TimeSlot
from apps.intake.models import IntakeSubmission

from . import queue
from .models import Appointment, Patient

PHONE_RE = re.compile(r"^\+?[0-9]{10,15}$")


def normalize_phone(value):
    phone = re.sub(r"[\s\-()]", "", value or "")
    if not PHONE_RE.match(phone):
        raise serializers.ValidationError("Enter a valid phone number, e.g. +77011234567.")
    # Kazakhstan: 8XXXXXXXXXX → +7XXXXXXXXXX
    if phone.startswith("8") and len(phone) == 11:
        phone = "+7" + phone[1:]
    if not phone.startswith("+"):
        phone = "+" + phone
    return phone


class PatientInputSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=200)
    phone = serializers.CharField(max_length=32)

    def validate_full_name(self, value):
        value = " ".join(value.split())
        if len(value) < 2:
            raise serializers.ValidationError("Enter your name.")
        return value

    def validate_phone(self, value):
        return normalize_phone(value)


class AppointmentCreateSerializer(serializers.Serializer):
    intake_id = serializers.PrimaryKeyRelatedField(source="intake", queryset=IntakeSubmission.objects.all())
    slot_id = serializers.PrimaryKeyRelatedField(source="slot", queryset=TimeSlot.objects.select_related("doctor"))
    # Optional: the patient may adjust the suggested specialist (UC-1 step 3).
    specialty_code = serializers.SlugField(required=False)
    patient = PatientInputSerializer()

    def validate(self, attrs):
        intake = attrs["intake"]
        slot = attrs["slot"]

        if hasattr(intake, "appointment"):
            raise serializers.ValidationError({"intake_id": "This intake was already used for a booking."})

        code = attrs.get("specialty_code") or intake.suggested_specialty.code
        try:
            specialty = Specialty.objects.get(clinic=intake.clinic, code=code)
        except Specialty.DoesNotExist:
            raise serializers.ValidationError({"specialty_code": "This clinic does not offer this specialty."})

        if slot.doctor.clinic_id != intake.clinic_id:
            raise serializers.ValidationError({"slot_id": "Slot belongs to another clinic."})
        if slot.doctor.specialty_id != specialty.id:
            raise serializers.ValidationError({"slot_id": "Slot does not match the chosen specialty."})
        if not slot.doctor.is_active:
            raise serializers.ValidationError({"slot_id": "This doctor is not available."})
        if slot.start <= timezone.now():
            raise serializers.ValidationError({"slot_id": "This slot is in the past."})

        attrs["specialty"] = specialty
        return attrs

    def create(self, validated_data):
        intake = validated_data["intake"]
        patient_data = validated_data["patient"]

        try:
            with transaction.atomic():
                slot = TimeSlot.objects.select_for_update().get(pk=validated_data["slot"].pk)
                if slot.is_booked:
                    raise serializers.ValidationError({"slot_id": "This slot was just taken. Please pick another one."})

                # Lock the doctor row so queue numbers are assigned sequentially.
                doctor = Doctor.objects.select_for_update().get(pk=slot.doctor_id)
                queue_date = timezone.localdate(slot.start)

                patient, created = Patient.objects.get_or_create(
                    phone=patient_data["phone"], defaults={"full_name": patient_data["full_name"]}
                )
                if not created and patient.full_name != patient_data["full_name"]:
                    patient.full_name = patient_data["full_name"]
                    patient.save(update_fields=["full_name"])

                appointment = Appointment.objects.create(
                    clinic=intake.clinic,
                    patient=patient,
                    doctor=doctor,
                    specialty=validated_data["specialty"],
                    slot=slot,
                    intake=intake,
                    urgency=intake.suggested_urgency,
                    queue_date=queue_date,
                    queue_number=queue.next_queue_number(doctor, queue_date),
                )
                slot.is_booked = True
                slot.save(update_fields=["is_booked"])
        except IntegrityError:
            raise serializers.ValidationError({"slot_id": "This slot was just taken. Please pick another one."})

        return appointment


class QueueInfoSerializer(serializers.Serializer):
    position = serializers.IntegerField(
        allow_null=True, help_text="1 = next in line, 0 = with the doctor now, null = not in the queue"
    )
    people_ahead = serializers.IntegerField()
    estimated_start = serializers.DateTimeField(allow_null=True)
    estimated_wait_minutes = serializers.IntegerField(allow_null=True)
    doctor_delay_minutes = serializers.IntegerField()


class AppointmentStatusSerializer(serializers.ModelSerializer):
    """Public view used by the patient tracking page (no personal data beyond first name)."""

    clinic_name = serializers.CharField(source="clinic.name", read_only=True)
    doctor_name = serializers.CharField(source="doctor.full_name", read_only=True)
    room = serializers.CharField(source="doctor.room", read_only=True)
    specialty = serializers.CharField(source="specialty.name", read_only=True)
    patient_first_name = serializers.SerializerMethodField()
    slot_start = serializers.DateTimeField(source="slot.start", read_only=True)
    queue = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "tracking_token",
            "status",
            "clinic_name",
            "doctor_name",
            "room",
            "specialty",
            "patient_first_name",
            "urgency",
            "urgency_confirmed",
            "queue_date",
            "queue_number",
            "slot_start",
            "queue",
        ]

    def get_patient_first_name(self, obj) -> str:
        return obj.patient.full_name.split()[0]

    @extend_schema_field(QueueInfoSerializer)
    def get_queue(self, obj):
        est = queue.estimate(obj, queue=self.context.get("queue"))
        return {
            "position": est.position,
            "people_ahead": est.people_ahead,
            "estimated_start": est.estimated_start,
            "estimated_wait_minutes": est.estimated_wait_minutes,
            "doctor_delay_minutes": est.doctor_delay_minutes,
        }


class StaffAppointmentSerializer(AppointmentStatusSerializer):
    patient_name = serializers.CharField(source="patient.full_name", read_only=True)
    patient_phone = serializers.CharField(source="patient.phone", read_only=True)
    suggested_urgency = serializers.CharField(source="intake.suggested_urgency", read_only=True, default=None)
    reasons = serializers.JSONField(source="intake.reasons", read_only=True, default=list)

    class Meta(AppointmentStatusSerializer.Meta):
        fields = ["id", "patient_name", "patient_phone", "suggested_urgency", "reasons"] + [
            f for f in AppointmentStatusSerializer.Meta.fields if f != "patient_first_name"
        ]


class StaffAppointmentUpdateSerializer(serializers.ModelSerializer):
    """Staff confirms/overrides urgency and moves the appointment through statuses."""

    urgency = serializers.ChoiceField(choices=Appointment.URGENCY_CHOICES, required=False)

    ALLOWED_TRANSITIONS = {
        Appointment.Status.BOOKED: {
            Appointment.Status.CHECKED_IN,
            Appointment.Status.NO_SHOW,
            Appointment.Status.CANCELLED,
        },
        Appointment.Status.CHECKED_IN: {Appointment.Status.IN_PROGRESS, Appointment.Status.CANCELLED},
        Appointment.Status.IN_PROGRESS: {Appointment.Status.COMPLETED},
    }

    class Meta:
        model = Appointment
        fields = ["urgency", "urgency_confirmed", "status"]

    def validate_status(self, value):
        current = self.instance.status
        if value != current and value not in self.ALLOWED_TRANSITIONS.get(current, set()):
            raise serializers.ValidationError(f"Cannot change status from '{current}' to '{value}'.")
        return value

    def update(self, instance, validated_data):
        # Changing urgency by staff counts as confirming it.
        if "urgency" in validated_data:
            validated_data.setdefault("urgency_confirmed", True)
        new_status = validated_data.get("status")
        if new_status == Appointment.Status.CHECKED_IN:
            instance.checked_in_at = timezone.now()
        with transaction.atomic():
            instance = super().update(instance, validated_data)
            if new_status in (Appointment.Status.CANCELLED, Appointment.Status.NO_SHOW):
                # Free the slot (no-show waitlist offering is Sprint 3+).
                TimeSlot.objects.filter(pk=instance.slot_id).update(is_booked=False)
        return instance
