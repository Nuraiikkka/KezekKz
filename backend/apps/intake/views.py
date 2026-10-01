from drf_spectacular.utils import OpenApiExample, extend_schema, inline_serializer
from rest_framework import serializers, status
from rest_framework.response import Response
from rest_framework.views import APIView

from . import questionnaire as q
from .serializers import IntakeCreateSerializer, IntakeResultSerializer


QuestionnaireSchema = inline_serializer(
    "Questionnaire",
    fields={
        "version": serializers.IntegerField(),
        "questions": serializers.ListField(child=serializers.DictField()),
    },
)

EXAMPLE_ANSWERS = {
    "clinic": "pilot-clinic",
    "answers": {
        "reason": "fever_cold",
        "preferred_specialty": "not_sure",
        "duration": "few_days",
        "pain_level": 3,
        "red_flags": ["high_fever"],
        "visit_type": "first",
        "preferred_time": "morning",
    },
}


class QuestionListView(APIView):
    authentication_classes = []

    @extend_schema(
        tags=["Intake"],
        summary="Intake questionnaire",
        description="The 8 intake questions. The frontend renders the form from this list.",
        responses=QuestionnaireSchema,
    )
    def get(self, request):
        return Response({"version": q.QUESTIONNAIRE_VERSION, "questions": q.QUESTIONS})


class IntakeCreateView(APIView):
    authentication_classes = []

    @extend_schema(
        tags=["Intake"],
        summary="Submit answers, get routing suggestion",
        description=(
            "Validates the answers and returns a suggested specialist and urgency level "
            "(routine / priority / urgent). This is a suggestion only — staff confirm urgency. "
            "`allergies_or_conditions` is accepted but never stored."
        ),
        request=IntakeCreateSerializer,
        responses={201: IntakeResultSerializer},
        examples=[OpenApiExample("Fever", value=EXAMPLE_ANSWERS, request_only=True)],
    )
    def post(self, request):
        serializer = IntakeCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        intake = serializer.save()
        return Response(IntakeResultSerializer(intake).data, status=status.HTTP_201_CREATED)
