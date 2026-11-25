from datetime import timedelta

from django.contrib.auth.models import User
from django.utils import timezone
from rest_framework.authtoken.models import Token

from apps.clinics.models import TimeSlot

from .models import Appointment, Patient
from .queue import get_no_show_risk
from .tests import BaseTest


class SmartFeaturesBase(BaseTest):
    def make_old(self, patient, status, minutes=None, days_ago=1):
        start = timezone.now() - timedelta(days=days_ago, minutes=len(Appointment.objects.all()))
        slot = TimeSlot.objects.create(doctor=self.doctor, start=start, end=start + timedelta(minutes=15), is_booked=True)
        data = {}
        if minutes:
            data = {"started_at": start, "finished_at": start + timedelta(minutes=minutes)}
        return Appointment.objects.create(
            patient=patient, doctor=self.doctor, slot=slot, urgency="routine", queue_number=1, status=status, **data
        )

    def staff(self):
        user = User.objects.create_user("nurse", password="pass", is_staff=True)
        token = Token.objects.create(user=user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Token {token.key}")


class RealDurationTests(SmartFeaturesBase):
    def test_wait_uses_real_visit_time(self):
        old_patient = Patient.objects.create(full_name="Old Patient", phone="+77000000001")
        for _ in range(3):
            self.make_old(old_patient, "completed", minutes=10)

        self.book(self.slots[0])
        second = self.book(self.slots[1], phone="+77011234568")
        queue = self.client.get(f"/api/appointments/{second.data['token']}/").data["queue"]

        self.assertTrue(queue["real_data"])
        self.assertEqual(queue["visit_minutes"], 10)
        self.assertEqual(queue["wait_minutes"], 10)

    def test_few_visits_use_default_time(self):
        old_patient = Patient.objects.create(full_name="Old Patient", phone="+77000000001")
        self.make_old(old_patient, "completed", minutes=10)

        response = self.book(self.slots[0])
        queue = self.client.get(f"/api/appointments/{response.data['token']}/").data["queue"]
        self.assertFalse(queue["real_data"])
        self.assertEqual(queue["visit_minutes"], 15)

    def test_staff_status_saves_times(self):
        response = self.book(self.slots[0])
        appointment = Appointment.objects.get(token=response.data["token"])
        self.staff()

        self.client.patch(f"/api/staff/appointments/{appointment.id}/", {"status": "in_progress"}, format="json")
        self.client.patch(f"/api/staff/appointments/{appointment.id}/", {"status": "completed"}, format="json")
        appointment.refresh_from_db()
        self.assertIsNotNone(appointment.started_at)
        self.assertIsNotNone(appointment.finished_at)


class NoShowRiskTests(SmartFeaturesBase):
    def test_new_patient_is_low_risk(self):
        response = self.book(self.slots[0])
        appointment = Appointment.objects.get(token=response.data["token"])
        self.assertEqual(get_no_show_risk(appointment), "low")

    def test_patient_with_no_shows_is_high_risk(self):
        response = self.book(self.slots[0])
        appointment = Appointment.objects.get(token=response.data["token"])
        self.make_old(appointment.patient, "no_show")
        self.make_old(appointment.patient, "no_show")
        self.assertEqual(get_no_show_risk(appointment), "high")

    def test_confirmation_lowers_risk(self):
        response = self.book(self.slots[0])
        appointment = Appointment.objects.get(token=response.data["token"])
        self.make_old(appointment.patient, "no_show")
        self.assertEqual(get_no_show_risk(appointment), "high")

        self.client.post(f"/api/appointments/{response.data['token']}/confirm/")
        appointment.refresh_from_db()
        self.assertTrue(appointment.patient_confirmed)
        self.assertEqual(get_no_show_risk(appointment), "low")

    def test_staff_sees_risk(self):
        self.book(self.slots[0])
        self.staff()
        day = timezone.localtime(self.slots[0].start).date()
        response = self.client.get(f"/api/staff/queue/?doctor={self.doctor.id}&date={day}")
        self.assertEqual(response.data[0]["no_show_risk"], "low")


class ArriveTests(SmartFeaturesBase):
    def test_too_early(self):
        response = self.book(self.slots[0])
        result = self.client.post(f"/api/appointments/{response.data['token']}/arrive/")
        self.assertEqual(result.status_code, 400)

    def test_check_in_near_the_time(self):
        slot = self.slots[0]
        slot.start = timezone.now() + timedelta(minutes=30)
        slot.end = slot.start + timedelta(minutes=15)
        slot.save()
        response = self.book(slot)
        result = self.client.post(f"/api/appointments/{response.data['token']}/arrive/")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["status"], "checked_in")


class BoardAndStatsTests(SmartFeaturesBase):
    def test_board_is_public_and_has_no_names(self):
        response = self.book(self.slots[0])
        Appointment.objects.filter(token=response.data["token"]).update(status="in_progress")
        result = self.client.get("/api/clinics/test/board/")
        self.assertEqual(result.status_code, 200)
        self.assertNotIn("Aru", str(result.data))

    def test_stats_need_staff(self):
        self.assertEqual(self.client.get("/api/staff/stats/").status_code, 401)

    def test_stats_numbers(self):
        patient = Patient.objects.create(full_name="Old Patient", phone="+77000000001")
        self.make_old(patient, "completed", minutes=10)
        self.make_old(patient, "no_show")
        self.staff()
        data = self.client.get("/api/staff/stats/").data
        self.assertEqual(data["completed"], 1)
        self.assertEqual(data["no_show"], 1)
        self.assertEqual(data["no_show_rate"], 50)
