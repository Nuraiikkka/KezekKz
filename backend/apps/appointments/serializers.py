from django.utils import timezone
from rest_framework import serializers

from apps.clinics.models import TimeSlot
from apps.intake.models import Intake

from .models import PAYMENT_METHODS, RECORD_KINDS, Appointment, MedicalRecord, Patient, Payment
from .payments import luhn_ok
from .queue import get_no_show_risk, get_queue_info, next_queue_number


def normalize_phone(value):
    phone = value.replace(" ", "").replace("-", "")
    if phone.startswith("8"):
        phone = "+7" + phone[1:]
    if len(phone) != 12 or not phone.startswith("+7") or not phone[1:].isdigit():
        raise serializers.ValidationError("Enter a phone like +77011234567.")
    return phone


class PatientInputSerializer(serializers.Serializer):
    full_name = serializers.CharField(max_length=200, error_messages={"required": "Name is required."})
    phone = serializers.CharField(max_length=20, error_messages={"required": "Phone number is required."})

    def validate_phone(self, value):
        return normalize_phone(value)


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
            raise serializers.ValidationError({"slot_id": "This slot is not free anymore."})
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

        conditions = data["intake"].answers.get("conditions_text", "")
        if conditions and not patient.conditions:
            patient.conditions = conditions
            patient.save()

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
    visit_minutes = serializers.IntegerField(allow_null=True)
    real_data = serializers.BooleanField()


class PaymentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Payment
        fields = ["method", "amount", "status", "card_last4", "receipt_number", "paid_at"]


class AppointmentSerializer(serializers.ModelSerializer):
    clinic = serializers.CharField(source="doctor.clinic.name")
    doctor = serializers.CharField(source="doctor.full_name")
    room = serializers.CharField(source="doctor.room")
    specialty = serializers.CharField(source="doctor.specialty.name")
    specialty_code = serializers.CharField(source="doctor.specialty.code")
    clinic_slug = serializers.CharField(source="doctor.clinic.slug")
    clinic_address = serializers.CharField(source="doctor.clinic.address")
    slot_start = serializers.DateTimeField(source="slot.start")
    first_name = serializers.SerializerMethodField()
    queue = serializers.SerializerMethodField()
    price = serializers.IntegerField(source="doctor.specialty.price")
    payment = PaymentSerializer(read_only=True, allow_null=True)
    offer = serializers.SerializerMethodField()
    telegram_connected = serializers.SerializerMethodField()
    has_profile = serializers.SerializerMethodField()

    class Meta:
        model = Appointment
        fields = [
            "token",
            "status",
            "queue_number",
            "urgency",
            "urgency_confirmed",
            "rating",
            "rating_comment",
            "patient_confirmed",
            "wants_earlier",
            "price",
            "payment",
            "offer",
            "telegram_connected",
            "has_profile",
            "clinic",
            "doctor",
            "room",
            "specialty",
            "specialty_code",
            "clinic_slug",
            "clinic_address",
            "slot_start",
            "first_name",
            "queue",
        ]

    def get_first_name(self, appointment) -> str:
        return appointment.patient.full_name.split()[0]

    def get_queue(self, appointment) -> QueueInfoSerializer:
        return get_queue_info(appointment)

    def get_has_profile(self, appointment) -> bool:
        return bool(appointment.patient.pin_hash)

    def get_telegram_connected(self, appointment) -> bool:
        return bool(appointment.patient.telegram_chat_id)

    def get_offer(self, appointment) -> dict:
        slot = appointment.offered_slot
        if slot is None:
            return None
        return {
            "slot_start": slot.start,
            "doctor": slot.doctor.full_name,
            "room": slot.doctor.room,
            "minutes_left": max(0, 10 - int((timezone.now() - appointment.offered_at).total_seconds() // 60)),
        }


class StaffAppointmentSerializer(AppointmentSerializer):
    patient_name = serializers.CharField(source="patient.full_name")
    patient_phone = serializers.CharField(source="patient.phone")
    reasons = serializers.JSONField(source="intake.reasons", default=list)
    patient_id = serializers.IntegerField(source="patient.id")
    no_show_risk = serializers.SerializerMethodField()
    intake_summary = serializers.SerializerMethodField()

    class Meta(AppointmentSerializer.Meta):
        fields = ["id", "patient_id", "patient_name", "patient_phone", "reasons", "no_show_risk", "intake_summary"] + AppointmentSerializer.Meta.fields

    def get_no_show_risk(self, appointment) -> str:
        return get_no_show_risk(appointment)

    def get_intake_summary(self, appointment) -> dict:
        answers = appointment.intake.answers if appointment.intake else {}
        keys = ["reason", "reason_text", "duration", "pain_level", "symptoms", "symptoms_text", "has_conditions", "conditions_text", "visit_type"]
        return {key: answers.get(key) for key in keys if answers.get(key) not in (None, "", [])}


class StaffUpdateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Appointment
        fields = ["urgency", "urgency_confirmed", "status"]


class RatingSerializer(serializers.Serializer):
    rating = serializers.IntegerField(min_value=1, max_value=5)
    comment = serializers.CharField(max_length=500, required=False, allow_blank=True)


class EarlierSerializer(serializers.Serializer):
    wants = serializers.BooleanField()


class PaySerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=[code for code, name in PAYMENT_METHODS])
    card_number = serializers.CharField(required=False, allow_blank=True)
    iin = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data["method"] == "card":
            number = data.get("card_number", "").replace(" ", "")
            if len(number) != 16 or not number.isdigit() or not luhn_ok(number):
                raise serializers.ValidationError({"card_number": "Enter a valid card number."})
            data["card_number"] = number
        if data["method"] == "insurance":
            iin = data.get("iin", "").replace(" ", "")
            if len(iin) != 12 or not iin.isdigit():
                raise serializers.ValidationError({"iin": "IIN must have 12 digits."})
            data["iin"] = iin
        return data


class StaffPaySerializer(serializers.Serializer):
    method = serializers.ChoiceField(choices=[code for code, name in PAYMENT_METHODS])
    iin = serializers.CharField(required=False, allow_blank=True)

    def validate(self, data):
        if data["method"] == "insurance":
            iin = data.get("iin", "").replace(" ", "")
            if len(iin) != 12 or not iin.isdigit():
                raise serializers.ValidationError({"iin": "IIN must have 12 digits."})
            data["iin"] = iin
        return data


class PatientProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Patient
        fields = ["id", "full_name", "phone", "birth_date", "conditions"]
        read_only_fields = ["id", "phone"]


class MedicalRecordSerializer(serializers.ModelSerializer):
    class Meta:
        model = MedicalRecord
        fields = ["id", "kind", "title", "text", "author", "appointment", "created_at"]
        read_only_fields = ["id", "author", "created_at"]

    def validate_kind(self, value):
        if value not in [code for code, name in RECORD_KINDS]:
            raise serializers.ValidationError("Wrong kind.")
        return value


class PinSerializer(serializers.Serializer):
    pin = serializers.CharField()

    def validate_pin(self, value):
        if not value.isdigit() or not 4 <= len(value) <= 6:
            raise serializers.ValidationError("PIN must have 4 to 6 digits.")
        return value


class SetPinSerializer(PinSerializer):
    token = serializers.UUIDField()


class LoginSerializer(PinSerializer):
    phone = serializers.CharField()

    def validate_phone(self, value):
        return normalize_phone(value)


class RegisterSerializer(PinSerializer):
    full_name = serializers.CharField(max_length=200, error_messages={"required": "Name is required."})
    phone = serializers.CharField()

    def validate_phone(self, value):
        return normalize_phone(value)


class NonceSerializer(serializers.Serializer):
    nonce = serializers.CharField(max_length=40)
