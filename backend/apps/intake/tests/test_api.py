from django.urls import reverse
from rest_framework.test import APITestCase

from apps.clinics.models import Clinic, Specialty
from apps.intake.models import IntakeSubmission

from .test_routing import answers


class IntakeApiTests(APITestCase):
    @classmethod
    def setUpTestData(cls):
        cls.clinic = Clinic.objects.create(name="Test Clinic", slug="test")
        Specialty.objects.create(clinic=cls.clinic, code="general_practitioner", name="GP")
        Specialty.objects.create(clinic=cls.clinic, code="cardiologist", name="Cardiologist")

    def test_questions_endpoint(self):
        res = self.client.get(reverse("intake-questions"))
        self.assertEqual(res.status_code, 200)
        self.assertEqual(len(res.data["questions"]), 8)

    def test_submit_intake_returns_suggestion(self):
        res = self.client.post(
            reverse("intake-create"), {"clinic": "test", "answers": answers(red_flags=["chest_pain"])}, format="json"
        )
        self.assertEqual(res.status_code, 201, res.data)
        self.assertEqual(res.data["suggested_specialty"]["code"], "cardiologist")
        self.assertEqual(res.data["suggested_urgency"], "urgent")
        self.assertIn("disclaimer", res.data)

    def test_free_text_health_info_is_not_stored(self):
        res = self.client.post(
            reverse("intake-create"),
            {"clinic": "test", "answers": answers(allergies_or_conditions="penicillin")},
            format="json",
        )
        self.assertEqual(res.status_code, 201)
        intake = IntakeSubmission.objects.get(pk=res.data["id"])
        self.assertNotIn("allergies_or_conditions", intake.answers)

    def test_validation_errors(self):
        bad = answers(pain_level=9, red_flags=["none", "chest_pain"], reason="nope")
        del bad["duration"]
        bad["diagnosis"] = "x"
        res = self.client.post(reverse("intake-create"), {"clinic": "test", "answers": bad}, format="json")
        self.assertEqual(res.status_code, 400)
        errors = res.data["answers"]
        for key in ("pain_level", "red_flags", "reason", "duration", "diagnosis"):
            self.assertIn(key, errors)

    def test_unknown_clinic(self):
        res = self.client.post(reverse("intake-create"), {"clinic": "nope", "answers": answers()}, format="json")
        self.assertEqual(res.status_code, 400)
