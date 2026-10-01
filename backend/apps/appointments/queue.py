"""
Queue foundation: queue numbering, live position and basic wait-time estimate.

Ordering inside one doctor's day queue:
  1. appointment slot time (patients come at their booked time),
  2. urgency (urgent before priority before routine for the same time),
  3. booking time.

Urgent cases are additionally offered the earliest free slot at booking
time (UC-1 alternate flow). Staff re-ranking and delay recalculation are
Sprint 3 work and will build on `ordered_queue()` / `estimate()`.
"""

from dataclasses import dataclass
from datetime import timedelta

from django.db.models import Max
from django.utils import timezone

from apps.intake.routing import URGENCY_RANK

from .models import Appointment


def next_queue_number(doctor, queue_date):
    """Must be called inside a transaction holding a lock on the doctor row."""
    current = Appointment.objects.filter(doctor=doctor, queue_date=queue_date).aggregate(m=Max("queue_number"))["m"]
    return (current or 0) + 1


def _sort_key(appointment):
    return (appointment.slot.start, URGENCY_RANK[appointment.urgency], appointment.created_at)


def ordered_queue(doctor, queue_date):
    """Active appointments of a doctor's day, in serving order."""
    appointments = list(
        Appointment.objects.filter(
            doctor=doctor, queue_date=queue_date, status__in=Appointment.ACTIVE_STATUSES
        ).select_related("slot", "patient", "specialty", "clinic", "intake")
    )
    # A patient currently with the doctor is always first.
    appointments.sort(key=lambda a: (a.status != Appointment.Status.IN_PROGRESS, *_sort_key(a)))
    return appointments


@dataclass
class QueueEstimate:
    position: int | None  # 0 = currently with the doctor, None = not in the queue
    people_ahead: int
    estimated_start: object  # datetime | None
    estimated_wait_minutes: int | None
    doctor_delay_minutes: int


def estimate(appointment, now=None, queue=None):
    """
    Basic wait-time estimate.

      estimated_start = max(slot start, now + people_ahead × avg consultation) + doctor delay
    """
    now = now or timezone.now()
    delay = appointment.doctor.current_delay_minutes

    if not appointment.is_active:
        return QueueEstimate(None, 0, None, None, delay)

    queue = queue if queue is not None else ordered_queue(appointment.doctor, appointment.queue_date)
    ids = [a.id for a in queue]
    index = ids.index(appointment.id) if appointment.id in ids else len(ids)

    if appointment.status == Appointment.Status.IN_PROGRESS:
        return QueueEstimate(0, 0, now, 0, delay)

    ahead = queue[:index]
    avg = appointment.specialty.avg_consultation_minutes
    by_queue = now + timedelta(minutes=avg * len(ahead))
    start = max(appointment.slot.start, by_queue) + timedelta(minutes=delay)
    wait = max(0, int((start - now).total_seconds() // 60))

    return QueueEstimate(
        position=index + 1,
        people_ahead=len(ahead),
        estimated_start=start,
        estimated_wait_minutes=wait,
        doctor_delay_minutes=delay,
    )
