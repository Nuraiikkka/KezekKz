from datetime import timedelta

from django.utils import timezone

from apps.clinics.models import Doctor, TimeSlot

from .models import Appointment, FamilyMember
from .test_smart_features import SmartFeaturesBase


class FamilyAndHelpBase(SmartFeaturesBase):
    def login(self):
        first = self.book(self.slots[0])
        session = self.client.post("/api/patient/pin/", {"token": first.data["token"], "pin": "4321"}, format="json")
        self.header = {"HTTP_X_PATIENT_TOKEN": session.data["token"]}
        return first

    def add_child(self, **extra):
        data = {"full_name": "Little Aru", "birth_date": "2018-05-01", "relation": "child", **extra}
        return self.client.post("/api/patient/family/", data, format="json", **self.header)

    def booking_data(self, slot, **extra):
        return {
            "intake_id": self.make_intake(),
            "slot_id": slot.id,
            "patient": {"full_name": "Aru Test", "phone": "+77011234567"},
            **extra,
        }


class FamilyTests(FamilyAndHelpBase):
    def test_add_and_list_family(self):
        self.login()
        created = self.add_child()
        self.assertEqual(created.status_code, 201)
        self.assertGreaterEqual(created.data["age"], 0)
        listed = self.client.get("/api/patient/family/", **self.header)
        self.assertEqual(len(listed.data), 1)
        self.assertEqual(self.client.get("/api/patient/me/", **self.header).data["family"][0]["full_name"], "Little Aru")

    def test_family_needs_login(self):
        self.assertEqual(self.client.get("/api/patient/family/").status_code, 401)

    def test_future_birth_date_is_rejected(self):
        self.login()
        future = (timezone.localdate() + timedelta(days=5)).isoformat()
        self.assertEqual(self.add_child(birth_date=future).status_code, 400)

    def test_book_for_a_child(self):
        self.login()
        member_id = self.add_child().data["id"]
        result = self.client.post(
            "/api/appointments/", self.booking_data(self.slots[1], family_member_id=member_id), format="json", **self.header
        )
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.data["for_member"]["name"], "Little Aru")
        self.assertEqual(result.data["for_member"]["relation"], "child")

    def test_booking_for_family_needs_the_patient_token(self):
        self.login()
        member_id = self.add_child().data["id"]
        result = self.client.post("/api/appointments/", self.booking_data(self.slots[1], family_member_id=member_id), format="json")
        self.assertEqual(result.status_code, 400)

    def test_cannot_use_a_member_of_another_patient(self):
        self.login()
        other = self.book(self.slots[1], phone="+77011234999")
        stranger = FamilyMember.objects.create(
            patient=Appointment.objects.get(token=other.data["token"]).patient, full_name="Not Yours", birth_date="2015-01-01"
        )
        result = self.client.post(
            "/api/appointments/", self.booking_data(self.slots[2], family_member_id=stranger.id), format="json", **self.header
        )
        self.assertEqual(result.status_code, 400)

    def test_delete_member_keeps_the_visit(self):
        self.login()
        member_id = self.add_child().data["id"]
        booked = self.client.post(
            "/api/appointments/", self.booking_data(self.slots[1], family_member_id=member_id), format="json", **self.header
        )
        self.assertEqual(self.client.delete(f"/api/patient/family/{member_id}/", **self.header).status_code, 204)
        self.assertEqual(Appointment.objects.filter(token=booked.data["token"]).count(), 1)

    def test_staff_sees_who_the_visit_is_for(self):
        self.login()
        member_id = self.add_child().data["id"]
        self.client.post(
            "/api/appointments/", self.booking_data(self.slots[1], family_member_id=member_id), format="json", **self.header
        )
        self.staff()
        queue = self.client.get(f"/api/staff/queue/?doctor={self.doctor.id}").data
        self.assertTrue(any(item["for_member"] for item in queue))


class NeedsTests(FamilyAndHelpBase):
    def test_help_needs_are_saved_and_shown(self):
        needs = {"wheelchair": True, "interpreter": True, "language": "kk"}
        result = self.client.post("/api/appointments/", self.booking_data(self.slots[0], needs=needs), format="json")
        self.assertEqual(result.status_code, 201)
        self.assertEqual(result.data["needs"], {"wheelchair": True, "interpreter": True, "language": "kk"})
        self.staff()
        queue = self.client.get(f"/api/staff/queue/?doctor={self.doctor.id}").data
        self.assertTrue(queue[0]["needs"]["wheelchair"])

    def test_no_needs_by_default(self):
        result = self.book(self.slots[0])
        self.assertEqual(result.data["needs"], {})

    def test_wrong_language_is_rejected(self):
        result = self.client.post("/api/appointments/", self.booking_data(self.slots[0], needs={"language": "xx"}), format="json")
        self.assertEqual(result.status_code, 400)


class MoveTests(FamilyAndHelpBase):
    def test_move_to_another_time(self):
        booked = self.book(self.slots[0])
        result = self.client.post(f"/api/appointments/{booked.data['token']}/move/", {"slot_id": self.slots[2].id}, format="json")
        self.assertEqual(result.status_code, 200)
        self.slots[0].refresh_from_db()
        self.slots[2].refresh_from_db()
        self.assertFalse(self.slots[0].is_booked)
        self.assertTrue(self.slots[2].is_booked)

    def test_switch_to_another_doctor_of_the_same_specialty(self):
        other = Doctor.objects.create(clinic=self.clinic, specialty=self.doctor.specialty, full_name="Dr. Other", room="2")
        start = timezone.now() + timedelta(hours=1)
        slot = TimeSlot.objects.create(doctor=other, start=start, end=start + timedelta(minutes=15))
        booked = self.book(self.slots[0])
        result = self.client.post(f"/api/appointments/{booked.data['token']}/move/", {"slot_id": slot.id}, format="json")
        self.assertEqual(result.status_code, 200)
        self.assertEqual(result.data["doctor"], "Dr. Other")

    def test_cannot_move_to_another_specialty(self):
        booked = self.book(self.slots[0])
        result = self.client.post(f"/api/appointments/{booked.data['token']}/move/", {"slot_id": self.cardio_slot.id}, format="json")
        self.assertEqual(result.status_code, 400)

    def test_cannot_move_to_a_taken_slot(self):
        first = self.book(self.slots[0])
        self.book(self.slots[1], phone="+77011234568")
        result = self.client.post(f"/api/appointments/{first.data['token']}/move/", {"slot_id": self.slots[1].id}, format="json")
        self.assertEqual(result.status_code, 400)

    def test_cannot_move_after_check_in(self):
        booked = self.book(self.slots[0])
        Appointment.objects.filter(token=booked.data["token"]).update(status="checked_in")
        result = self.client.post(f"/api/appointments/{booked.data['token']}/move/", {"slot_id": self.slots[2].id}, format="json")
        self.assertEqual(result.status_code, 400)

    def test_delay_is_visible_to_the_patient(self):
        booked = self.book(self.slots[0])
        self.doctor.delay_minutes = 20
        self.doctor.save()
        self.assertEqual(self.client.get(f"/api/appointments/{booked.data['token']}/").data["doctor_delay"], 20)
