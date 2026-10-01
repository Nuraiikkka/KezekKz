from datetime import timedelta

from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils import timezone
from rest_framework.authtoken.models import Token
from rest_framework.test import APITestCase

from apps.appointments.models import Appointment
from apps.clinics.models import Clinic, Doctor, Specialty, TimeSlot
from apps.intake.tests.test_routing import answers


class BookingTestBase(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.clinic = Clinic.objects.create(name="Test Clinic", slug="test")
        cls.gp = Specialty.objects.create(
            clinic=cls.clinic, code="general_practitioner", name="GP", avg_consultation_minutes=15
        )
        cls.cardio = Specialty.objects.create(clinic=cls.clinic, code="cardiologist", name="Cardiologist")
        cls.doctor = Doctor.objects.create(clinic=cls.clinic, specialty=cls.gp, full_name="Dr. GP", room="1")
        cls.cardiologist = Doctor.objects.create(clinic=cls.clinic, specialty=cls.cardio, full_name="Dr. Heart")
        base = timezone.now().replace(microsecond=0) + timedelta(hours=2)
        cls.slots = [
            TimeSlot.objects.create(
                doctor=cls.doctor, start=base + timedelta(minutes=15 * i), end=base + timedelta(minutes=15 * (i + 1))
            )
            for i in range(3)
        ]
        cls.past_slot = TimeSlot.objects.create(
            doctor=cls.doctor, start=base - timedelta(days=1), end=base - timedelta(days=1) + timedelta(minutes=15)
        )

    def intake(self, **overrides):
        res = self.client.post(
            reverse("intake-create"), {"clinic": "test", "answers": answers(**overrides)}, format="json"
        )
        assert res.status_code == 201, res.data
        return res.data["id"]

    def book(self, slot, phone="+77011234567", **kwargs):
        payload = {
            "intake_id": kwargs.pop("intake_id", None) or self.intake(),
            "slot_id": slot.id,
            "patient": {"full_name": "Aru Test", "phone": phone},
            **kwargs,
        }
        return self.client.post(reverse("appointment-create"), payload, format="json")


class BookingApiTests(BookingTestBase):
    def test_available_slots(self):
        res = self.client.get(reverse("slot-list", args=["test"]), {"specialty": "general_practitioner"})
        self.assertEqual(res.status_code, 200)
        self.assertEqual([s["id"] for s in res.data], [s.id for s in self.slots])

    def test_slots_require_specialty(self):
        self.assertEqual(self.client.get(reverse("slot-list", args=["test"])).status_code, 400)

    def test_book_and_track(self):
        res = self.book(self.slots[0])
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["queue_number"], 1)
        self.assertEqual(res.data["status"], "booked")
        self.assertFalse(res.data["urgency_confirmed"])
        self.assertEqual(res.data["patient_first_name"], "Aru")
        self.assertEqual(res.data["queue"]["position"], 1)
        self.assertTrue(TimeSlot.objects.get(pk=self.slots[0].pk).is_booked)

        track = self.client.get(reverse("appointment-track", args=[res.data["tracking_token"]]))
        self.assertEqual(track.status_code, 200)
        self.assertEqual(track.data["queue_number"], 1)
        self.assertNotIn("patient_phone", track.data)

    def test_queue_numbers_and_positions(self):
        first = self.book(self.slots[1], phone="+77010000001").data
        second = self.book(self.slots[0], phone="+77010000002").data
        self.assertEqual(first["queue_number"], 1)
        self.assertEqual(second["queue_number"], 2)
        # Earlier slot is served first regardless of booking order.
        first = self.client.get(reverse("appointment-track", args=[first["tracking_token"]])).data
        self.assertEqual(first["queue"]["position"], 2)
        self.assertEqual(first["queue"]["people_ahead"], 1)

    def test_slot_cannot_be_double_booked(self):
        self.assertEqual(self.book(self.slots[0]).status_code, 201)
        res = self.book(self.slots[0], phone="+77019999999")
        self.assertEqual(res.status_code, 400)
        self.assertIn("slot_id", res.data)

    def test_intake_cannot_be_reused(self):
        intake_id = self.intake()
        self.assertEqual(self.book(self.slots[0], intake_id=intake_id).status_code, 201)
        self.assertEqual(self.book(self.slots[1], intake_id=intake_id).status_code, 400)

    def test_slot_must_match_specialty(self):
        res = self.book(self.slots[0], intake_id=self.intake(red_flags=["chest_pain"]))
        self.assertEqual(res.status_code, 400)
        # Patient adjusts the suggestion to GP (UC-1 step 3).
        res = self.book(
            self.slots[0], intake_id=self.intake(red_flags=["chest_pain"]), specialty_code="general_practitioner"
        )
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["urgency"], "urgent")

    def test_past_slot_rejected(self):
        self.assertEqual(self.book(self.past_slot).status_code, 400)

    def test_phone_normalized(self):
        res = self.book(self.slots[0], phone="8 701 123 45 67")
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(Appointment.objects.get().patient.phone, "+77011234567")

    def test_invalid_phone(self):
        self.assertEqual(self.book(self.slots[0], phone="abc").status_code, 400)

    def test_cancel_frees_slot(self):
        token = self.book(self.slots[0]).data["tracking_token"]
        res = self.client.post(reverse("appointment-cancel", args=[token]))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(res.data["status"], "cancelled")
        self.assertIsNone(res.data["queue"]["position"])
        self.assertFalse(TimeSlot.objects.get(pk=self.slots[0].pk).is_booked)
        # Slot can be booked again.
        self.assertEqual(self.book(self.slots[0], phone="+77015555555").status_code, 201)

    def test_doctor_delay_increases_estimate(self):
        token = self.book(self.slots[0]).data["tracking_token"]
        before = self.client.get(reverse("appointment-track", args=[token])).data["queue"]["estimated_wait_minutes"]
        Doctor.objects.filter(pk=self.doctor.pk).update(current_delay_minutes=30)
        after = self.client.get(reverse("appointment-track", args=[token])).data["queue"]["estimated_wait_minutes"]
        self.assertGreaterEqual(after - before, 29)


class StaffApiTests(BookingTestBase):
    def setUp(self):
        user = get_user_model().objects.create_user("reception", password="x", is_staff=True)
        self.token = Token.objects.create(user=user)

    def auth(self):
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {self.token.key}")

    def test_queue_requires_staff(self):
        res = self.client.get(reverse("staff-queue"), {"doctor": self.doctor.id})
        self.assertEqual(res.status_code, 401)

    def test_staff_queue_and_confirm_urgency(self):
        self.book(self.slots[0])
        self.auth()
        day = timezone.localdate(self.slots[0].start).isoformat()
        res = self.client.get(reverse("staff-queue"), {"doctor": self.doctor.id, "date": day})
        self.assertEqual(res.status_code, 200)
        appt = res.data["appointments"][0]
        self.assertEqual(appt["patient_phone"], "+77011234567")

        res = self.client.patch(
            reverse("staff-appointment-update", args=[appt["id"]]), {"urgency": "priority"}, format="json"
        )
        self.assertEqual(res.status_code, 200, res.data)
        self.assertEqual(res.data["urgency"], "priority")
        self.assertTrue(res.data["urgency_confirmed"])

    def test_status_transitions(self):
        self.book(self.slots[0])
        appt = Appointment.objects.get()
        self.auth()
        url = reverse("staff-appointment-update", args=[appt.id])
        self.assertEqual(self.client.patch(url, {"status": "completed"}, format="json").status_code, 400)
        self.assertEqual(self.client.patch(url, {"status": "checked_in"}, format="json").status_code, 200)
        self.assertEqual(self.client.patch(url, {"status": "in_progress"}, format="json").status_code, 200)
        res = self.client.patch(url, {"status": "completed"}, format="json")
        self.assertEqual(res.data["status"], "completed")

    def test_no_show_frees_slot(self):
        self.book(self.slots[0])
        self.auth()
        url = reverse("staff-appointment-update", args=[Appointment.objects.get().id])
        self.assertEqual(self.client.patch(url, {"status": "no_show"}, format="json").status_code, 200)
        self.assertFalse(TimeSlot.objects.get(pk=self.slots[0].pk).is_booked)
