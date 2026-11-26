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
    telegram_chat_id = models.CharField(max_length=40, blank=True, default="")
    pin_hash = models.CharField(max_length=200, blank=True, default="")
    api_token = models.CharField(max_length=64, blank=True, default="", db_index=True)
    birth_date = models.DateField(null=True, blank=True)
    conditions = models.TextField(blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.full_name


RELATIONS = [
    ("child", "Child"),
    ("parent", "Parent"),
    ("spouse", "Spouse"),
    ("other", "Other"),
]


class FamilyMember(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="family")
    full_name = models.CharField(max_length=200)
    birth_date = models.DateField()
    relation = models.CharField(max_length=20, choices=RELATIONS, default="child")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.full_name


class Appointment(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="appointments")
    family_member = models.ForeignKey(FamilyMember, on_delete=models.SET_NULL, null=True, blank=True, related_name="appointments")
    needs = models.JSONField(default=dict, blank=True)
    doctor = models.ForeignKey(Doctor, on_delete=models.CASCADE, related_name="appointments")
    slot = models.ForeignKey(TimeSlot, on_delete=models.CASCADE, related_name="appointments")
    intake = models.OneToOneField(Intake, on_delete=models.SET_NULL, null=True, blank=True)
    urgency = models.CharField(max_length=20, choices=URGENCY_CHOICES)
    urgency_confirmed = models.BooleanField(default=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="booked")
    queue_number = models.IntegerField()
    rating = models.IntegerField(null=True, blank=True)
    rating_comment = models.TextField(blank=True, default="")
    patient_confirmed = models.BooleanField(default=False)
    wants_earlier = models.BooleanField(default=False)
    offered_slot = models.ForeignKey(TimeSlot, on_delete=models.SET_NULL, null=True, blank=True, related_name="offers")
    offered_at = models.DateTimeField(null=True, blank=True)
    notified_soon = models.BooleanField(default=False)
    started_at = models.DateTimeField(null=True, blank=True)
    finished_at = models.DateTimeField(null=True, blank=True)
    final_price = models.IntegerField(null=True, blank=True)
    token = models.UUIDField(default=uuid.uuid4, unique=True, editable=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["slot__start"]

    def __str__(self):
        return f"#{self.queue_number} {self.patient}"


PAYMENT_METHODS = [
    ("card", "Bank card"),
    ("kaspi", "Kaspi QR"),
    ("apple_pay", "Apple Pay"),
    ("google_pay", "Google Pay"),
    ("cash", "Cash at the cashier"),
    ("insurance", "OSMS insurance"),
]

PAYABLE_STATUSES = ["completed"]

RECORD_KINDS = [
    ("note", "Doctor's note"),
    ("analysis", "Analysis result"),
    ("prescription", "Prescription"),
]


class Payment(models.Model):
    appointment = models.OneToOneField(Appointment, on_delete=models.CASCADE, related_name="payment")
    method = models.CharField(max_length=20, choices=PAYMENT_METHODS)
    amount = models.IntegerField()
    status = models.CharField(max_length=20, default="paid")
    card_last4 = models.CharField(max_length=4, blank=True, default="")
    receipt_number = models.CharField(max_length=30)
    paid_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.receipt_number} {self.method} {self.amount}"


class MedicalRecord(models.Model):
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, related_name="records")
    appointment = models.ForeignKey(Appointment, on_delete=models.SET_NULL, null=True, blank=True, related_name="records")
    kind = models.CharField(max_length=20, choices=RECORD_KINDS, default="note")
    title = models.CharField(max_length=200)
    text = models.TextField(blank=True, default="")
    author = models.CharField(max_length=100, blank=True, default="")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.patient} {self.title}"


class TelegramLogin(models.Model):
    nonce = models.CharField(max_length=40, unique=True)
    chat_id = models.CharField(max_length=40, blank=True, default="")
    patient = models.ForeignKey(Patient, on_delete=models.CASCADE, null=True, blank=True, related_name="telegram_logins")
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.nonce
