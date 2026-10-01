from django.db import models

from apps.clinics.models import Clinic, Specialty

from .routing import URGENCY_LEVELS


class IntakeSubmission(models.Model):
    """
    Answers to the intake questionnaire + the routing suggestion.

    Only routing-relevant answers are stored (no diagnoses, no free-text
    health information — see questionnaire.NOT_PERSISTED_KEYS).
    """

    URGENCY_CHOICES = [(level, level.title()) for level in URGENCY_LEVELS]

    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="intakes")
    questionnaire_version = models.PositiveSmallIntegerField()
    answers = models.JSONField()
    suggested_specialty = models.ForeignKey(Specialty, on_delete=models.PROTECT, related_name="+")
    suggested_urgency = models.CharField(max_length=16, choices=URGENCY_CHOICES)
    urgency_score = models.PositiveSmallIntegerField(default=0)
    reasons = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Intake #{self.pk} → {self.suggested_specialty.code} / {self.suggested_urgency}"
