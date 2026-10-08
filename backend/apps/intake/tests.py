from django.test import TestCase
from rest_framework.test import APITestCase

from apps.clinics.models import Clinic, Specialty

from .models import Intake
from .routing import get_specialty, get_urgency

ALL_CODES = ["general_practitioner", "pediatrician", "cardiologist", "dermatologist"]


def make_answers(**changes):
    answers = {
        "reason": "general_checkup",
        "preferred_specialty": "not_sure",
        "duration": "more_than_week",
        "pain_level": 1,
        "red_flags": ["none"],
        "visit_type": "first",
        "preferred_time": "no_preference",
    }
    answers.update(changes)
    return answers


class RoutingTests(TestCase):
    def test_no_symptoms_is_routine(self):
        urgency, reasons = get_urgency(make_answers())
        self.assertEqual(urgency, "routine")

    def test_chest_pain_is_urgent(self):
        urgency, reasons = get_urgency(make_answers(red_flags=["chest_pain"]))
        self.assertEqual(urgency, "urgent")

    def test_high_fever_is_priority(self):
        urgency, reasons = get_urgency(make_answers(red_flags=["high_fever"]))
        self.assertEqual(urgency, "priority")

    def test_strong_pain_is_priority(self):
        urgency, reasons = get_urgency(make_answers(pain_level=4))
        self.assertEqual(urgency, "priority")

    def test_chest_pain_goes_to_cardiologist(self):
        self.assertEqual(get_specialty(make_answers(red_flags=["chest_pain"]), ALL_CODES), "cardiologist")

    def test_preferred_specialty(self):
        self.assertEqual(get_specialty(make_answers(preferred_specialty="dermatologist"), ALL_CODES), "dermatologist")

    def test_not_sure_goes_to_gp(self):
        self.assertEqual(get_specialty(make_answers(), ALL_CODES), "general_practitioner")

    def test_clinic_without_gp(self):
        self.assertEqual(get_specialty(make_answers(), ["pediatrician"]), "pediatrician")


class IntakeApiTests(APITestCase):
    def setUp(self):
        self.clinic = Clinic.objects.create(name="Test Clinic", slug="test")
        Specialty.objects.create(clinic=self.clinic, code="general_practitioner", name="GP")
        Specialty.objects.create(clinic=self.clinic, code="cardiologist", name="Cardiologist")

    def send(self, answers):
        return self.client.post("/api/intake/", {"clinic": "test", "answers": answers}, format="json")

    def test_get_questions(self):
        response = self.client.get("/api/intake/questions/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 8)

    def test_send_answers(self):
        response = self.send(make_answers(red_flags=["chest_pain"]))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["specialty"]["code"], "cardiologist")
        self.assertEqual(response.data["urgency"], "urgent")

    def test_allergies_are_not_saved(self):
        response = self.send(make_answers(allergies_or_conditions="penicillin"))
        self.assertEqual(response.status_code, 201)
        intake = Intake.objects.get(id=response.data["id"])
        self.assertNotIn("allergies_or_conditions", intake.answers)

    def test_wrong_answers(self):
        answers = make_answers(pain_level=9, reason="nope")
        del answers["duration"]
        response = self.send(answers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("pain_level", response.data["answers"])
        self.assertIn("reason", response.data["answers"])
        self.assertIn("duration", response.data["answers"])
