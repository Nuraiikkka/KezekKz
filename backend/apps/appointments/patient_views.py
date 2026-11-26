import secrets
from datetime import timedelta

from django.contrib.auth.hashers import check_password, make_password
from django.conf import settings
from django.db.models import Q
from django.utils import timezone
from django.shortcuts import get_object_or_404
from drf_spectacular.utils import extend_schema
from rest_framework.permissions import IsAdminUser
from rest_framework.response import Response
from rest_framework.throttling import ScopedRateThrottle
from rest_framework.views import APIView

from .models import Appointment, MedicalRecord, Patient, TelegramLogin
from .serializers import (
    AppointmentSerializer,
    LoginSerializer,
    MedicalRecordSerializer,
    NonceSerializer,
    PinSerializer,
    PatientProfileSerializer,
    RegisterSerializer,
    SetPinSerializer,
    StaffAppointmentSerializer,
)


def get_patient(request):
    token = request.headers.get("X-Patient-Token", "")
    if not token:
        return None
    return Patient.objects.filter(api_token=token).first()


def last_visit(patient):
    visit = patient.appointments.filter(status__in=["checked_in", "in_progress", "completed"]).order_by("-slot__start").first()
    return visit.slot.start if visit else None


def card(patient, staff=False):
    visits = patient.appointments.select_related("doctor", "slot").order_by("-slot__start")
    serializer = StaffAppointmentSerializer if staff else AppointmentSerializer
    return {
        "profile": PatientProfileSerializer(patient).data,
        "last_visit": last_visit(patient),
        "visits": serializer(visits, many=True).data,
        "records": MedicalRecordSerializer(patient.records.all(), many=True).data,
    }


def open_session(patient):
    patient.api_token = secrets.token_hex(24)
    patient.save()
    return {"token": patient.api_token, **card(patient)}


class PatientSetPinView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(request=SetPinSerializer, responses=dict)
    def post(self, request):
        serializer = SetPinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = get_object_or_404(Appointment, token=serializer.validated_data["token"])
        patient = appointment.patient
        if patient.pin_hash:
            return Response({"pin": ["The profile already has a PIN. Please log in."]}, status=400)

        patient.pin_hash = make_password(serializer.validated_data["pin"])
        patient.save()
        return Response(open_session(patient), status=201)


class PatientRegisterView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(request=RegisterSerializer, responses=dict)
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        data = serializer.validated_data

        patient, created = Patient.objects.get_or_create(phone=data["phone"], defaults={"full_name": data["full_name"]})
        if patient.pin_hash:
            return Response({"phone": ["A profile with this phone already exists. Please log in."]}, status=400)

        patient.pin_hash = make_password(data["pin"])
        if not patient.full_name:
            patient.full_name = data["full_name"]
        patient.save()
        return Response(open_session(patient), status=201)


class TelegramLoginStartView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(request=None, responses=dict)
    def post(self, request):
        if not settings.TELEGRAM_BOT_USERNAME:
            return Response({"detail": "Telegram login is not set up."}, status=400)
        nonce = secrets.token_hex(8)
        TelegramLogin.objects.create(nonce=nonce)
        return Response({"nonce": nonce, "link": f"https://t.me/{settings.TELEGRAM_BOT_USERNAME}?start=login_{nonce}"})


class TelegramLoginCheckView(APIView):
    @extend_schema(request=NonceSerializer, responses=dict)
    def post(self, request):
        serializer = NonceSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        login = TelegramLogin.objects.filter(nonce=serializer.validated_data["nonce"]).first()
        if login is None or login.created_at < timezone.now() - timedelta(minutes=10):
            return Response({"detail": "The login link has expired."}, status=400)
        if login.patient is None:
            return Response({"waiting": True})

        patient = login.patient
        login.delete()
        return Response(open_session(patient))


class PatientLoginView(APIView):
    throttle_classes = [ScopedRateThrottle]
    throttle_scope = "login"

    @extend_schema(request=LoginSerializer, responses=dict)
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient = Patient.objects.filter(phone=serializer.validated_data["phone"]).first()
        if patient is None or not patient.pin_hash:
            return Response({"detail": "Wrong phone or PIN."}, status=400)
        if not check_password(serializer.validated_data["pin"], patient.pin_hash):
            return Response({"detail": "Wrong phone or PIN."}, status=400)
        return Response(open_session(patient))


class PatientMeView(APIView):
    @extend_schema(responses=dict)
    def get(self, request):
        patient = get_patient(request)
        if patient is None:
            return Response({"detail": "Please log in."}, status=401)
        return Response(card(patient))

    @extend_schema(request=PatientProfileSerializer, responses=dict)
    def patch(self, request):
        patient = get_patient(request)
        if patient is None:
            return Response({"detail": "Please log in."}, status=401)
        serializer = PatientProfileSerializer(patient, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(card(patient))


class PatientChangePinView(APIView):
    @extend_schema(request=PinSerializer, responses=dict)
    def post(self, request):
        patient = get_patient(request)
        if patient is None:
            return Response({"detail": "Please log in."}, status=401)
        serializer = PinSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        patient.pin_hash = make_password(serializer.validated_data["pin"])
        patient.save()
        return Response({"ok": True})


class StaffPatientListView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses=PatientProfileSerializer(many=True))
    def get(self, request):
        query = request.query_params.get("q", "").strip()
        patients = Patient.objects.all()
        if query:
            patients = patients.filter(Q(full_name__icontains=query) | Q(phone__icontains=query))
        return Response(PatientProfileSerializer(patients.order_by("full_name")[:30], many=True).data)


class StaffPatientDetailView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(responses=dict)
    def get(self, request, pk):
        return Response(card(get_object_or_404(Patient, id=pk), staff=True))


class StaffRecordCreateView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=MedicalRecordSerializer, responses=dict)
    def post(self, request, pk):
        patient = get_object_or_404(Patient, id=pk)
        serializer = MedicalRecordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        appointment = serializer.validated_data.get("appointment")
        if appointment is not None and appointment.patient_id != patient.id:
            return Response({"appointment": ["This visit belongs to another patient."]}, status=400)
        serializer.save(patient=patient, author=request.user.username)
        return Response(card(patient, staff=True), status=201)


class StaffResetPinView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(request=None, responses=dict)
    def post(self, request, pk):
        patient = get_object_or_404(Patient, id=pk)
        patient.pin_hash = ""
        patient.api_token = ""
        patient.save()
        return Response(card(patient, staff=True))
