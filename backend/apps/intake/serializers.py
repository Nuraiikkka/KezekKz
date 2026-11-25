from rest_framework import serializers

from apps.clinics.models import Clinic
from apps.clinics.serializers import SpecialtySerializer

from .models import Intake
from .questionnaire import QUESTIONS
from .routing import need_emergency


def check_answers(answers):
    errors = {}
    keys = [question["key"] for question in QUESTIONS]

    for key in answers:
        if key not in keys:
            errors[key] = "Unknown question."

    for question in QUESTIONS:
        key = question["key"]
        value = answers.get(key)

        if value is None or value == "" or value == []:
            if question["required"]:
                errors[key] = "This question is required."
            continue

        options = [option["value"] for option in question.get("options", [])]

        if question["type"] == "single_choice" and value not in options:
            errors[key] = "Wrong answer."

        if question["type"] == "multi_choice":
            if not isinstance(value, list) or any(item not in options for item in value):
                errors[key] = "Wrong answer."

        if question["type"] == "scale":
            if not isinstance(value, int) or value < 1 or value > 5:
                errors[key] = "Must be from 1 to 5."

    return errors


class IntakeInputSerializer(serializers.Serializer):
    clinic = serializers.SlugRelatedField(slug_field="slug", queryset=Clinic.objects.all())
    answers = serializers.DictField()

    def validate_answers(self, answers):
        errors = check_answers(answers)
        if errors:
            raise serializers.ValidationError(errors)
        return answers


class IntakeSerializer(serializers.ModelSerializer):
    specialty = SpecialtySerializer()
    call_103 = serializers.SerializerMethodField()
    earliest_slot = serializers.SerializerMethodField()
    preferred_time = serializers.SerializerMethodField()

    class Meta:
        model = Intake
        fields = ["id", "specialty", "urgency", "reasons", "call_103", "earliest_slot", "preferred_time"]

    def get_call_103(self, intake) -> bool:
        return need_emergency(intake.answers)

    def get_earliest_slot(self, intake) -> bool:
        return intake.urgency == "urgent"

    def get_preferred_time(self, intake) -> str:
        return intake.answers.get("preferred_time", "no_preference")
