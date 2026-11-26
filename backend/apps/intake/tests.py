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
        "has_conditions": "no",
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
        self.assertEqual(len(response.data), 9)

    def test_send_answers(self):
        response = self.send(make_answers(red_flags=["chest_pain"]))
        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.data["specialty"]["code"], "cardiologist")
        self.assertEqual(response.data["urgency"], "urgent")

    def test_other_reason_needs_a_description(self):
        response = self.send(make_answers(reason="other"))
        self.assertEqual(response.status_code, 400)
        self.assertIn("reason_text", response.data["answers"])

        response = self.send(make_answers(reason="other", reason_text="Pain when I sit"))
        self.assertEqual(response.status_code, 201)

    def test_conditions_yes_needs_a_text(self):
        response = self.send(make_answers(has_conditions="yes"))
        self.assertEqual(response.status_code, 400)

        response = self.send(make_answers(has_conditions="yes", conditions_text="Penicillin allergy"))
        self.assertEqual(response.status_code, 201)
        intake = Intake.objects.get(id=response.data["id"])
        self.assertEqual(intake.answers["conditions_text"], "Penicillin allergy")

    def test_symptoms_are_saved_with_a_note(self):
        answers = make_answers(symptoms=["rectal_pain", "constipation"], symptoms_text="Since Monday")
        response = self.send(answers)
        self.assertEqual(response.status_code, 201)
        self.assertEqual(Intake.objects.get(id=response.data["id"]).answers["symptoms"], ["rectal_pain", "constipation"])

    def test_wrong_symptom(self):
        self.assertEqual(self.send(make_answers(symptoms=["magic"])).status_code, 400)

    def test_questions_use_the_specialties_of_the_clinic(self):
        response = self.client.get("/api/intake/questions/?clinic=test")
        options = [item["value"] for item in response.data[1]["options"]]
        self.assertEqual(options, ["general_practitioner", "cardiologist", "not_sure"])

    def test_wrong_answers(self):
        answers = make_answers(pain_level=9, reason="nope")
        del answers["duration"]
        response = self.send(answers)
        self.assertEqual(response.status_code, 400)
        self.assertIn("pain_level", response.data["answers"])
        self.assertIn("reason", response.data["answers"])
        self.assertIn("duration", response.data["answers"])
