from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path
from drf_spectacular.utils import extend_schema, inline_serializer
from drf_spectacular.views import SpectacularAPIView, SpectacularRedocView, SpectacularSwaggerView
from rest_framework import serializers
from rest_framework.authtoken.views import ObtainAuthToken

from apps.appointments import views as appointment_views
from apps.clinics import views as clinic_views
from apps.intake import views as intake_views


def health(request):
    return JsonResponse({"status": "ok"})


class StaffTokenView(ObtainAuthToken):
    @extend_schema(
        tags=["Staff"],
        summary="Get staff API token",
        description="Use the returned token as `Authorization: Token <token>`.",
        request=inline_serializer(
            "TokenRequest", fields={"username": serializers.CharField(), "password": serializers.CharField()}
        ),
        responses=inline_serializer("TokenResponse", fields={"token": serializers.CharField()}),
    )
    def post(self, request, *args, **kwargs):
        return super().post(request, *args, **kwargs)


api_urls = [
    path("health/", health, name="health"),
    # docs
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    path("docs/", SpectacularSwaggerView.as_view(url_name="schema"), name="swagger-ui"),
    path("redoc/", SpectacularRedocView.as_view(url_name="schema"), name="redoc"),
    # auth (staff)
    path("auth/token/", StaffTokenView.as_view(), name="auth-token"),
    # clinics
    path("clinics/", clinic_views.ClinicListView.as_view(), name="clinic-list"),
    path("clinics/<slug:slug>/", clinic_views.ClinicDetailView.as_view(), name="clinic-detail"),
    path("clinics/<slug:slug>/specialties/", clinic_views.SpecialtyListView.as_view(), name="specialty-list"),
    path("clinics/<slug:slug>/doctors/", clinic_views.DoctorListView.as_view(), name="doctor-list"),
    path("clinics/<slug:slug>/slots/", clinic_views.AvailableSlotListView.as_view(), name="slot-list"),
    # intake
    path("intake/questions/", intake_views.QuestionListView.as_view(), name="intake-questions"),
    path("intake/", intake_views.IntakeCreateView.as_view(), name="intake-create"),
    # appointments (patient)
    path("appointments/", appointment_views.AppointmentCreateView.as_view(), name="appointment-create"),
    path(
        "appointments/track/<uuid:token>/",
        appointment_views.AppointmentTrackView.as_view(),
        name="appointment-track",
    ),
    path(
        "appointments/track/<uuid:token>/cancel/",
        appointment_views.AppointmentCancelView.as_view(),
        name="appointment-cancel",
    ),
    # staff
    path("staff/queue/", appointment_views.StaffQueueView.as_view(), name="staff-queue"),
    path(
        "staff/appointments/<int:pk>/",
        appointment_views.StaffAppointmentUpdateView.as_view(),
        name="staff-appointment-update",
    ),
]

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include(api_urls)),
]
