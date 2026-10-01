from django.contrib import admin

from .models import IntakeSubmission


@admin.register(IntakeSubmission)
class IntakeSubmissionAdmin(admin.ModelAdmin):
    list_display = ["id", "clinic", "suggested_specialty", "suggested_urgency", "urgency_score", "created_at"]
    list_filter = ["clinic", "suggested_urgency"]
    readonly_fields = ["answers", "reasons", "created_at"]
