from django.conf import settings
from django.db import models


class Clinic(models.Model):
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    address = models.CharField(max_length=300, blank=True)
    phone = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name


class Specialty(models.Model):
    """A specialty offered by a clinic (taken from the pilot clinic's list)."""

    # Stable codes used by the routing rules in apps.intake.routing.
    GENERAL_PRACTITIONER = "general_practitioner"
    PEDIATRICIAN = "pediatrician"
    CARDIOLOGIST = "cardiologist"
    DERMATOLOGIST = "dermatologist"

    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="specialties")
    code = models.SlugField(max_length=64)
    name = models.CharField(max_length=120)
    avg_consultation_minutes = models.PositiveSmallIntegerField(
        default=settings.KEZEK_DEFAULT_CONSULTATION_MINUTES
    )

    class Meta:
        ordering = ["name"]
        constraints = [
            models.UniqueConstraint(fields=["clinic", "code"], name="unique_specialty_code_per_clinic"),
        ]
        verbose_name_plural = "specialties"

    def __str__(self):
        return f"{self.name} ({self.clinic.name})"


class Doctor(models.Model):
    clinic = models.ForeignKey(Clinic, on_delete=models.CASCADE, related_name="doctors")
    specialty = models.ForeignKey(Specialty, on_delete=models.PROTECT, related_name="doctors")
    full_name = models.CharField(max_length=200)
    room = models.CharField(max_length=32, blank=True)
    is_active = models.BooleanField(default=True)
    # Set by staff when a doctor is running late; used in wait-time estimates.
    current_delay_minutes = models.PositiveSmallIntegerField(default=0)

    class Meta:
        ordering = ["full_name"]

    def __str__(self):
        return f"{self.full_name} — {self.specialty.name}"


class TimeSlot(models.Model):
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="slots")
    start = models.DateTimeField()
    end = models.DateTimeField()
    is_booked = models.BooleanField(default=False)

    class Meta:
        ordering = ["start"]
        constraints = [
            models.UniqueConstraint(fields=["doctor", "start"], name="unique_slot_start_per_doctor"),
            models.CheckConstraint(condition=models.Q(end__gt=models.F("start")), name="slot_end_after_start"),
        ]
        indexes = [models.Index(fields=["doctor", "start"])]

    def __str__(self):
        return f"{self.doctor.full_name} @ {self.start:%Y-%m-%d %H:%M}"

    @property
    def duration_minutes(self):
        return int((self.end - self.start).total_seconds() // 60)
