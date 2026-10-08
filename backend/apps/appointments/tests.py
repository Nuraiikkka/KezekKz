from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.clinics.models import Clinic, Doctor, Specialty, TimeSlot
from apps.intake.tests import make_answers

from .models import Appointment


class BaseTest(APITestCase):
    def setUp(self):
        self.clinic = Clinic.objects.create(name="Test Clinic", slug="test")
        gp = Specialty.objects.create(clinic=self.clinic, code="general_practitioner", name="GP", visit_minutes=15)
        cardio = Specialty.objects.create(clinic=self.clinic, code="cardiologist", name="Cardiologist")
        self.doctor = Doctor.objects.create(clinic=self.clinic, specialty=gp, full_name="Dr. GP", room="1")
        cardiologist = Doctor.objects.create(clinic=self.clinic, specialty=cardio, full_name="Dr. Heart")

        start = timezone.now() + timedelta(hours=2)
        self.slots = []
        for i in range(3):
            slot_start = start + timedelta(minutes=15 * i)
            self.slots.append(
                TimeSlot.objects.create(doctor=self.doctor, start=slot_start, end=slot_start + timedelta(minutes=15))
            )
        self.cardio_slot = TimeSlot.objects.create(doctor=cardiologist, start=start, end=start + timedelta(minutes=25))
        self.old_slot = TimeSlot.objects.create(
            doctor=self.doctor, start=start - timedelta(days=1), end=start - timedelta(days=1) + timedelta(minutes=15)
        )

    def make_intake(self, **changes):
        response = self.client.post(
            "/api/intake/", {"clinic": "test", "answers": make_answers(**changes)}, format="json"
        )
        return response.data["id"]

    def book(self, slot, phone="+77011234567", intake_id=None, specialty_code=None):
        data = {
            "intake_id": intake_id or self.make_intake(),
            "slot_id": slot.id,
            "patient": {"full_name": "Aru Test", "phone": phone},
        }
        if specialty_code:
            data["specialty_code"] = specialty_code
        return self.client.post("/api/appointments/", data, format="json")


class BookingTests(BaseTest):
    def test_free_slots(self):
        response = self.client.get("/api/clinics/test/slots/?specialty=general_practitioner")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 3)

    def test_book_and_track(self):
        response = self.book(self.slots[0])
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["queue_number"], 1)
        self.assertEqual(response.data["first_name"], "Aru")
        self.assertEqual(response.data["queue"]["position"], 1)

        token = response.data["token"]
        response = self.client.get(f"/api/appointments/{token}/")
        self.assertEqual(response.status_code, 200)
        self.assertNotIn("patient_phone", response.data)

    def test_queue_position(self):
        later = self.book(self.slots[1], phone="+77010000001").data
        self.book(self.slots[0], phone="+77010000002")
        response = self.client.get(f"/api/appointments/{later['token']}/")
        self.assertEqual(response.data["queue"]["position"], 2)
        self.assertEqual(response.data["queue"]["wait_minutes"], 15)

    def test_slot_cannot_be_booked_twice(self):
        self.book(self.slots[0])
        response = self.book(self.slots[0], phone="+77019999999")
        self.assertEqual(response.status_code, 400)

    def test_intake_cannot_be_used_twice(self):
        intake_id = self.make_intake()
        self.assertEqual(self.book(self.slots[0], intake_id=intake_id).status_code, 201)
        self.assertEqual(self.book(self.slots[1], intake_id=intake_id).status_code, 400)

    def test_old_slot(self):
        self.assertEqual(self.book(self.old_slot).status_code, 400)

    def test_phone_with_8(self):
        response = self.book(self.slots[0], phone="8 701 123 45 67")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Appointment.objects.get().patient.phone, "+77011234567")

    def test_wrong_phone(self):
        self.assertEqual(self.book(self.slots[0], phone="abc").status_code, 400)

    def test_cancel(self):
        token = self.book(self.slots[0]).data["token"]
        response = self.client.post(f"/api/appointments/{token}/cancel/")
        self.assertEqual(response.data["status"], "cancelled")
        self.slots[0].refresh_from_db()
        self.assertFalse(self.slots[0].is_booked)

    def test_doctor_delay(self):
        token = self.book(self.slots[0]).data["token"]
        self.doctor.delay_minutes = 30
        self.doctor.save()
        response = self.client.get(f"/api/appointments/{token}/")
        self.assertEqual(response.data["queue"]["wait_minutes"], 30)


class StaffTests(BaseTest):
    def login(self):
        user = User.objects.create_user("reception", password="x", is_staff=True)
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION="Token " + token.key)

    def test_need_login(self):
        response = self.client.get(f"/api/staff/queue/?doctor={self.doctor.id}")
        self.assertEqual(response.status_code, 401)

    def test_queue_and_confirm_urgency(self):
        self.book(self.slots[0])
        self.login()
        day = timezone.localdate(self.slots[0].start)
        response = self.client.get(f"/api/staff/queue/?doctor={self.doctor.id}&date={day}")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data[0]["patient_phone"], "+77011234567")

        appointment_id = response.data[0]["id"]
        response = self.client.patch(f"/api/staff/appointments/{appointment_id}/", {"urgency": "priority"})
        self.assertEqual(response.data["urgency"], "priority")
        self.assertTrue(response.data["urgency_confirmed"])

    def test_no_show_frees_slot(self):
        self.book(self.slots[0])
        self.login()
        appointment = Appointment.objects.get()
        self.client.patch(f"/api/staff/appointments/{appointment.id}/", {"status": "no_show"})
        self.slots[0].refresh_from_db()
        self.assertFalse(self.slots[0].is_booked)
