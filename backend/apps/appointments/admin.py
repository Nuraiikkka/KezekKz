from django.contrib import admin

from .models import Appointment, Patient


@admin.register(Patient)
class PatientAdmin(admin.ModelAdmin):
    list_display = ["full_name", "phone", "created_at"]
    search_fields = ["full_name", "phone"]


@admin.register(Appointment)
class AppointmentAdmin(admin.ModelAdmin):
    list_display = ["queue_number", "queue_date", "patient", "doctor", "urgency", "urgency_confirmed", "status"]
    list_filter = ["queue_date", "status", "urgency", "doctor"]
    search_fields = ["patient__full_name", "patient__phone"]
    readonly_fields = ["tracking_token", "created_at", "updated_at"]
