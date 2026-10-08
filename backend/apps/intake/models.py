from django.db import models

from apps.clinics.models import Clinic, Specialty

URGENCY_CHOICES = [
    ("routine", "Routine"),
    ("priority", "Priority"),
    ("urgent", "Urgent"),
]


class Intake(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="intakes")
    answers = models.JSONField()
    specialty = models.ForeignKey(Specialty, on_delete=models.CASCADE)
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES)
    reasons = models.JSONField(default=list)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Intake {self.id} - {self.urgency}"
