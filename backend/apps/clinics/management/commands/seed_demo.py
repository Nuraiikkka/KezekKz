"""
Seed a pilot clinic with specialties, doctors, slots and a staff user.

    python manage.py seed_demo            # idempotent
    python manage.py seed_demo --days 14  # generate slots for 14 days
"""

from datetime import datetime, time, timedelta

from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone

from apps.clinics.models import Clinic, Doctor, Specialty, TimeSlot

SPECIALTIES = [
    ("general_practitioner", "General practitioner", 15),
    ("pediatrician", "Pediatrician", 20),
    ("cardiologist", "Cardiologist", 25),
    ("dermatologist", "Dermatologist", 20),
]

DOCTORS = [
    ("general_practitioner", "Dr. Aigerim Nurlanovna", "101"),
    ("general_practitioner", "Dr. Yerlan Bekov", "102"),
    ("pediatrician", "Dr. Dana Serikova", "201"),
    ("cardiologist", "Dr. Askar Tulegenov", "301"),
    ("dermatologist", "Dr. Madina Ospanova", "302"),
]

WORK_START = time(9, 0)
WORK_END = time(18, 0)
LUNCH = (time(13, 0), time(14, 0))


class Command(BaseCommand):
    help = "Seed demo data for the pilot clinic."

    def add_arguments(self, parser):
        parser.add_argument("--days", type=int, default=7)
        parser.add_argument("--staff-password", default="kezek-staff-2026")

    @transaction.atomic
    def handle(self, *args, days, staff_password, **options):
        clinic, _ = Clinic.objects.get_or_create(
            slug="pilot-clinic",
            defaults={"name": "Pilot Clinic Almaty", "address": "Almaty, Abay Ave 10", "phone": "+77270000000"},
        )

        specialties = {}
        for code, name, minutes in SPECIALTIES:
            specialties[code], _ = Specialty.objects.get_or_create(
                clinic=clinic, code=code, defaults={"name": name, "avg_consultation_minutes": minutes}
            )

        tz = timezone.get_current_timezone()
        today = timezone.localdate()
        created_slots = 0
        for code, full_name, room in DOCTORS:
            doctor, _ = Doctor.objects.get_or_create(
                clinic=clinic, full_name=full_name, defaults={"specialty": specialties[code], "room": room}
            )
            step = timedelta(minutes=doctor.specialty.avg_consultation_minutes)
            for offset in range(days):
                day = today + timedelta(days=offset)
                if day.weekday() == 6:  # closed on Sunday
                    continue
                cursor = timezone.make_aware(datetime.combine(day, WORK_START), tz)
                end_of_day = timezone.make_aware(datetime.combine(day, WORK_END), tz)
                while cursor + step <= end_of_day:
                    if not (LUNCH[0] <= cursor.astimezone(tz).time() < LUNCH[1]):
                        _, created = TimeSlot.objects.get_or_create(
                            doctor=doctor, start=cursor, defaults={"end": cursor + step}
                        )
                        created_slots += created
                    cursor += step

        User = get_user_model()
        staff, created = User.objects.get_or_create(username="reception", defaults={"is_staff": True})
        if created:
            staff.set_password(staff_password)
            staff.save()

        self.stdout.write(
            self.style.SUCCESS(
                f"Clinic '{clinic.slug}': {len(specialties)} specialties, {len(DOCTORS)} doctors, "
                f"{created_slots} new slots. Staff user: reception"
                + (f" / {staff_password}" if created else " (already existed)")
            )
        )
