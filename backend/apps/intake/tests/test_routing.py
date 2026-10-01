from django.test import SimpleTestCase

from apps.intake.routing import PRIORITY, ROUTINE, URGENT, route

ALL = ["general_practitioner", "pediatrician", "cardiologist", "dermatologist"]


def answers(**overrides):
    base = {
        "reason": "general_checkup",
        "preferred_specialty": "not_sure",
        "duration": "more_than_week",
        "pain_level": 1,
        "red_flags": ["none"],
        "visit_type": "first",
        "preferred_time": "no_preference",
    }
    base.update(overrides)
    return base


class UrgencyTests(SimpleTestCase):
    def test_no_symptoms_is_routine(self):
        self.assertEqual(route(answers(), ALL).urgency, ROUTINE)

    def test_chest_pain_is_urgent_and_routes_to_cardiologist(self):
        result = route(answers(red_flags=["chest_pain"]), ALL)
        self.assertEqual(result.urgency, URGENT)
        self.assertEqual(result.specialty_code, "cardiologist")
        self.assertTrue(result.offer_earliest_slot)
        self.assertFalse(result.emergency_advice)

    def test_breathing_difficulty_gives_emergency_advice(self):
        result = route(answers(red_flags=["difficulty_breathing"]), ALL)
        self.assertEqual(result.urgency, URGENT)
        self.assertTrue(result.emergency_advice)

    def test_high_fever_is_priority(self):
        self.assertEqual(route(answers(reason="fever_cold", red_flags=["high_fever"]), ALL).urgency, PRIORITY)

    def test_strong_pain_is_priority(self):
        self.assertEqual(route(answers(pain_level=4), ALL).urgency, PRIORITY)

    def test_max_pain_alone_is_priority_not_urgent(self):
        self.assertEqual(route(answers(pain_level=5), ALL).urgency, PRIORITY)

    def test_sudden_injury_with_max_pain_is_urgent(self):
        result = route(answers(reason="injury", duration="today", pain_level=5, red_flags=["high_fever"]), ALL)
        self.assertEqual(result.urgency, URGENT)


class SpecialtyTests(SimpleTestCase):
    def test_preferred_specialty_is_used(self):
        self.assertEqual(route(answers(preferred_specialty="dermatologist"), ALL).specialty_code, "dermatologist")

    def test_not_sure_defaults_to_gp(self):
        self.assertEqual(route(answers(), ALL).specialty_code, "general_practitioner")

    def test_unavailable_preference_falls_back_to_gp(self):
        result = route(answers(preferred_specialty="cardiologist"), ["general_practitioner"])
        self.assertEqual(result.specialty_code, "general_practitioner")

    def test_clinic_without_gp_uses_available_specialty(self):
        self.assertEqual(route(answers(), ["pediatrician"]).specialty_code, "pediatrician")
