from rest_framework import serializers

from apps.clinics.models import Clinic
from apps.clinics.serializers import SpecialtySerializer

from .models import Intake
from .questionnaire import ALL_SYMPTOMS, build_questions
from .routing import need_emergency


def check_answers(answers, clinic=None):
    errors = {}
    questions = build_questions(clinic)
    keys = [question["key"] for question in questions]
    text_keys = [question["followup"]["key"] for question in questions if question.get("followup")]

    for key in answers:
        if key not in keys and key not in text_keys:
            errors[key] = "Unknown question."

    for key in text_keys:
        value = answers.get(key)
        if value is not None and (not isinstance(value, str) or len(value) > 500):
            errors[key] = "Text is too long."

    for question in questions:
        key = question["key"]
        value = answers.get(key)
        followup = question.get("followup")

        if followup and not errors.get(followup["key"]):
            needed = followup["required"] and (followup["when"] is None or value in followup["when"])
            if needed and not str(answers.get(followup["key"], "")).strip():
                errors[followup["key"]] = "Please write a short description."

        if value is None or value == "" or value == []:
            if question["required"]:
                errors[key] = "This question is required."
            continue

        values = [option["value"] for option in question.get("options", [])]
        if question["type"] == "multi_choice" and key == "symptoms":
            values = ALL_SYMPTOMS

        if question["type"] == "single_choice" and value not in values:
            errors[key] = "Wrong answer."

        if question["type"] == "multi_choice":
            if not isinstance(value, list) or any(item not in values for item in value):
                errors[key] = "Wrong answer."

        if question["type"] == "scale":
            if not isinstance(value, int) or value < 1 or value > 5:
                errors[key] = "Must be from 1 to 5."

    return errors


class IntakeInputSerializer(serializers.Serializer):
    clinic = serializers.SlugRelatedField(slug_field="slug", queryset=Clinic.objects.all())
    answers = serializers.DictField()

    def validate(self, data):
        errors = check_answers(data["answers"], data["clinic"])
        if errors:
            raise serializers.ValidationError({"answers": errors})
        return data


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
