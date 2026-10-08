from apps.intake.models import Intake
from apps.intake.tests import make_answers

from .models import Appointment
from .tests import BaseTest


class US01BookAppointment(BaseTest):
    def test_happy_path(self):
        response = self.book(self.slots[0])
        self.assertEqual(response.status_code, 201)
        self.assertIn("queue_number", response.data)

    def test_slot_taken(self):
        self.book(self.slots[0])
        response = self.book(self.slots[0], phone="+77019999999")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["slot_id"][0], "This slot is not free anymore.")
        self.assertEqual(Appointment.objects.count(), 1)

    def test_missing_phone(self):
        data = {"intake_id": self.make_intake(), "slot_id": self.slots[0].id, "patient": {"full_name": "Aru"}}
        response = self.client.post("/api/appointments/", data, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.data["patient"]["phone"][0], "Phone number is required.")
        self.assertEqual(Appointment.objects.count(), 0)


class US02Questionnaire(BaseTest):
    def test_answers_saved_with_booking(self):
        self.book(self.slots[0])
        self.assertEqual(Appointment.objects.get().intake.answers["reason"], "general_checkup")

    def test_required_question(self):
        answers = make_answers()
        del answers["reason"]
        response = self.client.post("/api/intake/", {"clinic": "test", "answers": answers}, format="json")
        self.assertEqual(response.status_code, 400)
        self.assertEqual(Intake.objects.count(), 0)


class US03Suggestion(BaseTest):
    def send(self, **changes):
        response = self.client.post(
            "/api/intake/", {"clinic": "test", "answers": make_answers(**changes)}, format="json"
        )
        return response.data

    def test_red_flag(self):
        for flag in ["chest_pain", "difficulty_breathing"]:
            data = self.send(red_flags=[flag])
            self.assertEqual(data["urgency"], "urgent")
            self.assertTrue(data["earliest_slot"])

    def test_normal_case(self):
        data = self.send(reason="fever_cold", duration="few_days", pain_level=2)
        self.assertEqual(data["specialty"]["code"], "general_practitioner")
        self.assertEqual(data["urgency"], "routine")

    def test_not_sure_and_change_specialist(self):
        data = self.send(preferred_specialty="not_sure", reason="injury")
        self.assertEqual(data["specialty"]["code"], "general_practitioner")

        response = self.book(self.cardio_slot, intake_id=data["id"], specialty_code="cardiologist")
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["specialty"], "Cardiologist")
