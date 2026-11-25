from drf_spectacular.utils import extend_schema
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Intake
from .questionnaire import QUESTIONS
from .routing import get_specialty, get_urgency
from .serializers import IntakeInputSerializer, IntakeSerializer


class QuestionListView(APIView):
    @extend_schema(responses=dict)
    def get(self, request):
        return Response(QUESTIONS)


class IntakeCreateView(APIView):
    @extend_schema(request=IntakeInputSerializer, responses=IntakeSerializer)
    def post(self, request):
        serializer = IntakeInputSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        clinic = serializer.validated_data["clinic"]
        answers = serializer.validated_data["answers"]
        answers.pop("allergies_or_conditions", None)

        codes = list(clinic.specialties.values_list("code", flat=True))
        if not codes:
            return Response({"clinic": ["This clinic has no specialties."]}, status=400)

        urgency, reasons = get_urgency(answers)
        code = get_specialty(answers, codes)

        intake = Intake.objects.create(
            clinic=clinic,
            answers=answers,
            specialty=clinic.specialties.get(code=code),
            urgency=urgency,
            reasons=reasons,
        )
        return Response(IntakeSerializer(intake).data, status=201)
