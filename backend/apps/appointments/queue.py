from django.utils import timezone

from .models import ACTIVE_STATUSES, Appointment


def get_queue(doctor, day):
    return Appointment.objects.filter(
        doctor=doctor,
        slot__start__date=day,
        status__in=ACTIVE_STATUSES,
    ).order_by("slot__start", "created_at")


def next_queue_number(doctor, start):
    day = timezone.localdate(start)
    return Appointment.objects.filter(doctor=doctor, slot__start__date=day).count() + 1


def get_queue_info(appointment):
    if appointment.status not in ACTIVE_STATUSES:
        return {"position": None, "people_ahead": 0, "wait_minutes": None}

    day = timezone.localdate(appointment.slot.start)
    people_ahead = 0
    for item in get_queue(appointment.doctor, day):
        if item.id == appointment.id:
            break
        people_ahead += 1

    visit_minutes = appointment.doctor.specialty.visit_minutes
    wait = people_ahead * visit_minutes + appointment.doctor.delay_minutes

    return {"position": people_ahead + 1, "people_ahead": people_ahead, "wait_minutes": wait}
