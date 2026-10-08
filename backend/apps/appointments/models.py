import uuid

from django.db import models

from apps.clinics.models import Doctor, TimeSlot
from apps.intake.models import URGENCY_CHOICES, Intake

STATUS_CHOICES = [
    ("booked", "Booked"),
    ("checked_in", "Checked in"),
    ("in_progress", "In progress"),
    ("completed", "Completed"),
    ("no_show", "No-show"),
    ("cancelled", "Cancelled"),
]

ACTIVE_STATUSES = ["booked", "checked_in", "in_progress"]


class Patient(models.Model):
    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=20, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name="appointments")
    intake = models.OneToOneField(Intake, on_delete=models.SET_NULL, null=True, blank=True)
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES)
    urgency_confirmed = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="booked")
    queue_number = models.IntegerField()
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["slot__start"]

    def __str__(self):
        return f"#{self.queue_number} {self.patient}"
