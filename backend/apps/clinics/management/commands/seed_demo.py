import os
from datetime import datetime, time, timedelta

from django.contrib.auth.models import User
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.clinics.models import Clinic, Doctor, Specialty, TimeSlot

SPECIALTIES = [
    ("general_practitioner", "General practitioner", 15, 8000),
    ("pediatrician", "Pediatrician", 20, 9000),
    ("cardiologist", "Cardiologist", 25, 15000),
    ("dermatologist", "Dermatologist", 20, 12000),
]

DOCTORS = [
    ("general_practitioner", "Dr. Aigerim Nurlanovna", "101"),
    ("general_practitioner", "Dr. Yerlan Bekov", "102"),
    ("pediatrician", "Dr. Dana Serikova", "201"),
    ("cardiologist", "Dr. Askar Tulegenov", "301"),
    ("dermatologist", "Dr. Madina Ospanova", "302"),
]


class Command(BaseCommand):
    help = "Add demo clinic, doctors and free slots"

    def handle(self, *args, **options):
        clinic, _ = Clinic.objects.get_or_create(
            slug="pilot-clinic",
            defaults={"name": "Pilot Clinic Almaty", "address": "Almaty, Abay Ave 10"},
        )

        for code, name, minutes, price in SPECIALTIES:
            Specialty.objects.get_or_create(
                clinic=clinic, code=code, defaults={"name": name, "visit_minutes": minutes, "price": price}
            )

        today = timezone.localdate()
        for code, full_name, room in DOCTORS:
            specialty = Specialty.objects.get(clinic=clinic, code=code)
            doctor, _ = Doctor.objects.get_or_create(
                clinic=clinic, full_name=full_name, defaults={"specialty": specialty, "room": room}
            )
            step = timedelta(minutes=specialty.visit_minutes)

            for day_number in range(7):
                day = today + timedelta(days=day_number)
                if day.weekday() == 6:
                    continue
                start = timezone.make_aware(datetime.combine(day, time(9, 0)))
                end_of_day = timezone.make_aware(datetime.combine(day, time(18, 0)))
                while start + step <= end_of_day:
                    if timezone.localtime(start).hour != 13:
                        TimeSlot.objects.get_or_create(doctor=doctor, start=start, defaults={"end": start + step})
                    start = start + step

        password = os.getenv("STAFF_PASSWORD", "kezek-staff-2026")
        user, created = User.objects.get_or_create(username="reception", defaults={"is_staff": True})
        user.is_staff = True
        user.set_password(password)
        user.save()

        self.stdout.write(self.style.SUCCESS("Demo data is ready"))
