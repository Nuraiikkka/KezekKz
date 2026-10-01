from rest_framework import serializers

from apps.clinics.models import Clinic, Specialty
from apps.clinics.serializers import SpecialtySerializer

from . import questionnaire as q
from .models import IntakeSubmission
from .routing import route

DISCLAIMER = (
    "This is a suggestion only, not a medical decision. "
    "Clinic staff will confirm your urgency level."
)


def validate_answers(answers):
    if not isinstance(answers, dict):
        raise serializers.ValidationError("Answers must be an object.")

    errors = {}
    clean = {}

    unknown = set(answers) - set(q.QUESTIONS_BY_KEY)
    for key in unknown:
        errors[key] = "Unknown question."

    for question in q.QUESTIONS:
        key = question["key"]
        value = answers.get(key)

        if value in (None, "", []):
            if question["required"]:
                errors[key] = "This question is required."
            continue

        qtype = question["type"]
        if qtype == q.SINGLE:
            if value not in q.option_values(key):
                errors[key] = "Invalid option."
                continue
        elif qtype == q.MULTI:
            if not isinstance(value, list) or not set(value) <= q.option_values(key):
                errors[key] = "Must be a list of valid options."
                continue
            value = sorted(set(value))
            if "none" in value and len(value) > 1:
                errors[key] = "'none' cannot be combined with other options."
                continue
        elif qtype == q.SCALE:
            try:
                value = int(value)
            except (TypeError, ValueError):
                errors[key] = "Must be a number."
                continue
            if not question["min"] <= value <= question["max"]:
                errors[key] = f"Must be between {question['min']} and {question['max']}."
                continue
        elif qtype == q.TEXT:
            if not isinstance(value, str) or len(value) > question.get("max_length", 300):
                errors[key] = "Text is too long."
                continue

        clean[key] = value

    if errors:
        raise serializers.ValidationError(errors)
    return clean


class IntakeCreateSerializer(serializers.Serializer):
    clinic = serializers.SlugRelatedField(slug_field="slug", queryset=Clinic.objects.filter(is_active=True))
    answers = serializers.JSONField()

    def validate_answers(self, value):
        return validate_answers(value)

    def create(self, validated_data):
        clinic = validated_data["clinic"]
        answers = validated_data["answers"]
        specialties = {s.code: s for s in Specialty.objects.filter(clinic=clinic)}
        if not specialties:
            raise serializers.ValidationError({"clinic": "This clinic has no specialties configured."})

        result = route(answers, specialties.keys())
        stored_answers = {k: v for k, v in answers.items() if k not in q.NOT_PERSISTED_KEYS}

        intake = IntakeSubmission.objects.create(
            clinic=clinic,
            questionnaire_version=q.QUESTIONNAIRE_VERSION,
            answers=stored_answers,
            suggested_specialty=specialties[result.specialty_code],
            suggested_urgency=result.urgency,
            urgency_score=result.score,
            reasons=result.reasons,
        )
        intake.routing = result
        return intake


class IntakeResultSerializer(serializers.ModelSerializer):
    clinic = serializers.SlugRelatedField(slug_field="slug", read_only=True)
    suggested_specialty = SpecialtySerializer(read_only=True)
    emergency_advice = serializers.SerializerMethodField()
    offer_earliest_slot = serializers.SerializerMethodField()
    preferred_time = serializers.SerializerMethodField()
    disclaimer = serializers.SerializerMethodField()

    class Meta:
        model = IntakeSubmission
        fields = [
            "id",
            "clinic",
            "suggested_specialty",
            "suggested_urgency",
            "reasons",
            "emergency_advice",
            "offer_earliest_slot",
            "preferred_time",
            "disclaimer",
            "created_at",
        ]

    def _routing(self, obj):
        if not hasattr(obj, "routing"):
            specialties = Specialty.objects.filter(clinic=obj.clinic).values_list("code", flat=True)
            obj.routing = route(obj.answers, specialties)
        return obj.routing

    def get_emergency_advice(self, obj) -> bool:
        return self._routing(obj).emergency_advice

    def get_offer_earliest_slot(self, obj) -> bool:
        return self._routing(obj).offer_earliest_slot

    def get_preferred_time(self, obj) -> str:
        return obj.answers.get("preferred_time", "no_preference")

    def get_disclaimer(self, obj) -> str:
        return DISCLAIMER
