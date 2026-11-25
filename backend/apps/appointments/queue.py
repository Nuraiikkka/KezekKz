from django.utils import timezone

from .models import ACTIVE_STATUSES, Appointment

MIN_REAL_VISITS = 3
LAST_VISITS = 20


def get_queue(doctor, day):
    return Appointment.objects.filter(
        doctor=doctor,
        slot__start__date=day,
        status__in=ACTIVE_STATUSES,
    ).order_by("slot__start", "created_at")


def next_queue_number(doctor, start):
    day = timezone.localdate(start)
    return Appointment.objects.filter(doctor=doctor, slot__start__date=day).count() + 1


def get_visit_minutes(doctor):
    visits = Appointment.objects.filter(
        doctor=doctor,
        status="completed",
        started_at__isnull=False,
        finished_at__isnull=False,
    ).order_by("-finished_at")[:LAST_VISITS]

    minutes = []
    for visit in visits:
        value = (visit.finished_at - visit.started_at).total_seconds() / 60
        if 2 <= value <= 120:
            minutes.append(value)

    if len(minutes) >= MIN_REAL_VISITS:
        return round(sum(minutes) / len(minutes)), True
    return doctor.specialty.visit_minutes, False


def get_queue_info(appointment):
    if appointment.status not in ACTIVE_STATUSES:
        return {"position": None, "people_ahead": 0, "wait_minutes": None, "visit_minutes": None, "real_data": False}

    day = timezone.localdate(appointment.slot.start)
    people_ahead = 0
    for item in get_queue(appointment.doctor, day):
        if item.id == appointment.id:
            break
        people_ahead += 1

    visit_minutes, real_data = get_visit_minutes(appointment.doctor)
    wait = people_ahead * visit_minutes + appointment.doctor.delay_minutes

    return {
        "position": people_ahead + 1,
        "people_ahead": people_ahead,
        "wait_minutes": wait,
        "visit_minutes": visit_minutes,
        "real_data": real_data,
    }


def get_no_show_risk(appointment):
    points = 0

    patient = appointment.patient
    others = Appointment.objects.filter(patient=patient).exclude(id=appointment.id)
    no_shows = others.filter(status="no_show").count()
    points += min(no_shows * 2, 4)

    if not others.filter(status="completed").exists():
        points += 1

    lead = appointment.slot.start - appointment.created_at
    if lead.days >= 3:
        points += 1

    if appointment.patient_confirmed:
        points -= 2

    if points >= 3:
        return "high"
    if points >= 2:
        return "medium"
    return "low"
