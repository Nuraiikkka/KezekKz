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
    ("proctologist", "Proctologist", 20, 12000),
    ("neurologist", "Neurologist", 25, 13000),
    ("ent", "ENT specialist", 20, 10000),
    ("ophthalmologist", "Ophthalmologist", 20, 10000),
    ("gynecologist", "Gynecologist", 25, 12000),
    ("urologist", "Urologist", 20, 12000),
    ("endocrinologist", "Endocrinologist", 25, 13000),
    ("gastroenterologist", "Gastroenterologist", 25, 13000),
    ("orthopedist", "Orthopedist", 25, 12000),
]

DOCTORS = [
    ("general_practitioner", "Dr. Aigerim Nurlanovna", "101"),
    ("general_practitioner", "Dr. Yerlan Bekov", "102"),
    ("pediatrician", "Dr. Dana Serikova", "201"),
    ("cardiologist", "Dr. Askar Tulegenov", "301"),
    ("dermatologist", "Dr. Madina Ospanova", "302"),
    ("proctologist", "Dr. Nurlan Seitkali", "303"),
    ("neurologist", "Dr. Aliya Mukhametova", "304"),
    ("ent", "Dr. Timur Abenov", "305"),
    ("ophthalmologist", "Dr. Saule Karimova", "306"),
    ("gynecologist", "Dr. Gulnara Zhunusova", "401"),
    ("urologist", "Dr. Bakhyt Ismailov", "402"),
    ("endocrinologist", "Dr. Zarina Kassymova", "403"),
    ("gastroenterologist", "Dr. Ruslan Omarov", "404"),
    ("orthopedist", "Dr. Kairat Dosmailov", "405"),
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
            known = set(doctor.slots.filter(start__gte=timezone.now() - timedelta(days=1)).values_list("start", flat=True))
            new_slots = []

            for day_number in range(7):
                day = today + timedelta(days=day_number)
                if day.weekday() == 6:
                    continue
                start = timezone.make_aware(datetime.combine(day, time(9, 0)))
                end_of_day = timezone.make_aware(datetime.combine(day, time(18, 0)))
                while start + step <= end_of_day:
                    if timezone.localtime(start).hour != 13 and start not in known:
                        new_slots.append(TimeSlot(doctor=doctor, start=start, end=start + step))
                    start = start + step

            TimeSlot.objects.bulk_create(new_slots)

        password = os.getenv("STAFF_PASSWORD") or "kezek-staff-2026"
        user, created = User.objects.get_or_create(username="reception", defaults={"is_staff": True})
        user.is_staff = True
        user.set_password(password)
        user.save()

        self.stdout.write(self.style.SUCCESS("Demo data is ready"))
