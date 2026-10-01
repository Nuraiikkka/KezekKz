import uuid

from django.db import models

from apps.clinics.models import Clinic, Doctor, Specialty, TimeSlot
from apps.intake.models import IntakeSubmission
from apps.intake.routing import URGENCY_LEVELS


class Patient(models.Model):
    """Minimal contact data only — no health records (Charter privacy rule)."""

    full_name = models.CharField(max_length=200)
    phone = models.CharField(max_length=32, unique=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


class Appointment(models.Model):
    class Status(models.TextChoices):
        BOOKED = "booked", "Booked"
        CHECKED_IN = "checked_in", "Checked in"
        IN_PROGRESS = "in_progress", "In progress"
        COMPLETED = "completed", "Completed"
        NO_SHOW = "no_show", "No-show"
        CANCELLED = "cancelled", "Cancelled"

    # Statuses that still occupy a place in the live queue.
    ACTIVE_STATUSES = [Status.BOOKED, Status.CHECKED_IN, Status.IN_PROGRESS]

    URGENCY_CHOICES = [(level, level.title()) for level in URGENCY_LEVELS]

    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="appointments")
    patient = models.ForeignKey(Patient, on_delete=models.PROTECT, related_name="appointments")
    doctor = models.ForeignKey(Doctor, on_delete=models.PROTECT, related_name="appointments")
    specialty = models.ForeignKey(Specialty, on_delete=models.PROTECT, related_name="appointments")
    slot = models.ForeignKey(TimeSlot, on_delete=models.PROTECT, related_name="appointments")
    intake = models.OneToOneField(
        IntakeSubmission, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointment"
    )

    urgency = models.CharField(max_length=16, choices=URGENCY_CHOICES)
    # Urgency starts as the system suggestion; staff must confirm it.
    urgency_confirmed = models.BooleanField(default=False)
    status = models.CharField(max_length=16, choices=Status.choices, default=Status.BOOKED)

    queue_date = models.DateField()
    queue_number = models.PositiveIntegerField()
    tracking_token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    checked_in_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["slot__start"]
        constraints = [
            models.UniqueConstraint(
                fields=["doctor", "queue_date", "queue_number"], name="unique_queue_number_per_doctor_day"
            ),
            # A slot can hold only one active appointment.
            models.UniqueConstraint(
                fields=["slot"],
                condition=models.Q(status__in=["booked", "checked_in", "in_progress"]),
                name="one_active_appointment_per_slot",
            ),
        ]
        indexes = [models.Index(fields=["doctor", "queue_date", "status"])]

    def __str__(self):
        return f"#{self.queue_number} {self.patient} → {self.doctor.full_name} ({self.queue_date})"

    @property
    def is_active(self):
        return self.status in self.ACTIVE_STATUSES
