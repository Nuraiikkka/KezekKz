from django.contrib import admin

from .models import Clinic, Doctor, Specialty, TimeSlot


@admin.register(Clinic)
class ClinicAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "is_active"]
    prepopulated_fields = {"slug": ["name"]}


@admin.register(Specialty)
class SpecialtyAdmin(admin.ModelAdmin):
    list_display = ["name", "code", "clinic", "avg_consultation_minutes"]
    list_filter = ["clinic"]


@admin.register(Doctor)
class DoctorAdmin(admin.ModelAdmin):
    list_display = ["full_name", "specialty", "clinic", "room", "current_delay_minutes", "is_active"]
    list_filter = ["clinic", "specialty", "is_active"]


@admin.register(TimeSlot)
class TimeSlotAdmin(admin.ModelAdmin):
    list_display = ["doctor", "start", "end", "is_booked"]
    list_filter = ["is_booked", "doctor__specialty"]
    date_hierarchy = "start"
