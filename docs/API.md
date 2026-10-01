# KezekKz API contract

Interactive docs: `/api/docs/` (Swagger) · `/api/redoc/` · schema `/api/schema/`

Base URL: `/api/` · JSON only · Times are ISO-8601 with the clinic time zone (Asia/Almaty).

Patient endpoints are public (no login). The **tracking token** (UUID) returned on booking is the only
credential a patient needs to see or cancel their appointment. Staff endpoints need
`Authorization: Token <token>` from a user with `is_staff`.

Errors follow DRF format: `{"field": ["message"]}` or `{"detail": "message"}` with HTTP 400/401/403/404.

---

## Health

`GET /health/` → `{"status": "ok"}`

## Clinics

| Method | Path | Description |
|---|---|---|
| GET | `/clinics/` | Active clinics |
| GET | `/clinics/{slug}/` | One clinic |
| GET | `/clinics/{slug}/specialties/` | Specialties (`code`, `name`, `avg_consultation_minutes`) |
| GET | `/clinics/{slug}/doctors/?specialty=<code>` | Active doctors |
| GET | `/clinics/{slug}/slots/?specialty=<code>[&date=YYYY-MM-DD][&part_of_day=morning\|afternoon]` | Free future slots (next 7 days if no date), max 100, sorted by time |

Slot: `{"id", "doctor_id", "doctor_name", "start", "end"}`

## Intake (questionnaire + routing)

### `GET /intake/questions/`

```json
{ "version": 1, "questions": [ { "key": "reason", "text": "...", "type": "single_choice", "required": true, "options": [{"value": "fever_cold", "label": "Fever / cold"}] } ] }
```

Question types: `single_choice`, `multi_choice`, `scale` (`min`/`max`), `text` (`max_length`).
Keys: `reason`, `preferred_specialty`, `duration`, `pain_level`, `red_flags`, `visit_type`,
`allergies_or_conditions` (optional, **never stored**), `preferred_time`.

### `POST /intake/`

Request:
```json
{
  "clinic": "pilot-clinic",
  "answers": {
    "reason": "fever_cold",
    "preferred_specialty": "not_sure",
    "duration": "few_days",
    "pain_level": 3,
    "red_flags": ["high_fever"],
    "visit_type": "first",
    "preferred_time": "morning"
  }
}
```

Response `201`:
```json
{
  "id": 12,
  "clinic": "pilot-clinic",
  "suggested_specialty": {"id": 1, "code": "general_practitioner", "name": "General practitioner", "avg_consultation_minutes": 15},
  "suggested_urgency": "priority",
  "reasons": ["High fever reported", "General practitioner is the default first contact"],
  "emergency_advice": false,
  "offer_earliest_slot": false,
  "preferred_time": "morning",
  "disclaimer": "This is a suggestion only, not a medical decision. Clinic staff will confirm your urgency level.",
  "created_at": "..."
}
```

Validation errors are returned per question under `answers`, e.g. `{"answers": {"pain_level": "Must be between 1 and 5."}}`.

#### Routing rules (MVP — not clinically validated, staff always confirm)

| Rule | Score |
|---|---|
| Difficulty breathing / chest pain / severe bleeding | +10 |
| High fever | +4 |
| Pain 5 / 4 / 3 | +6 / +4 / +1 |
| Started today and pain ≥ 3 | +2 |
| Injury and pain ≥ 3 | +2 |

`score ≥ 10 → urgent`, `≥ 4 → priority`, else `routine`.
Specialty: chest pain → cardiologist; else the patient's preference; else general practitioner.
`emergency_advice` = breathing difficulty or severe bleeding (show "call 103").
`offer_earliest_slot` = urgent.

## Appointments (patient)

### `POST /appointments/`

```json
{
  "intake_id": 12,
  "slot_id": 345,
  "specialty_code": "general_practitioner",
  "patient": {"full_name": "Aru Serik", "phone": "+77011234567"}
}
```

`specialty_code` is optional (defaults to the suggestion; the patient may change it). The slot must
belong to that specialty, be free and in the future. One intake = one booking. Phone is normalized
(`8701…` → `+7701…`).

Response `201` — appointment status (same shape as tracking below).

### `GET /appointments/track/{token}/`

```json
{
  "tracking_token": "b3c1…",
  "status": "booked",
  "clinic_name": "Pilot Clinic Almaty",
  "doctor_name": "Dr. Yerlan Bekov",
  "room": "102",
  "specialty": "General practitioner",
  "patient_first_name": "Aru",
  "urgency": "priority",
  "urgency_confirmed": false,
  "queue_date": "2026-10-02",
  "queue_number": 3,
  "slot_start": "2026-10-02T10:15:00+05:00",
  "queue": {
    "position": 3,
    "people_ahead": 2,
    "estimated_start": "2026-10-02T10:15:00+05:00",
    "estimated_wait_minutes": 95,
    "doctor_delay_minutes": 0
  }
}
```

`queue.position` is `null` when the appointment is no longer active (completed / cancelled / no-show),
`0` when the patient is with the doctor.

### `POST /appointments/track/{token}/cancel/`

Only while `status = booked`. Frees the slot.

## Queue logic (Sprint 2 foundation)

- `queue_number`: sequential per doctor per day, assigned at booking.
- Serving order: in-progress first, then slot time, then urgency (urgent → priority → routine), then booking time.
- `estimated_start = max(slot start, now + people_ahead × avg consultation) + doctor delay`.

## Staff

| Method | Path | Description |
|---|---|---|
| POST | `/auth/token/` | `{"username", "password"}` → `{"token"}` |
| GET | `/staff/queue/?doctor=<id>[&date=YYYY-MM-DD]` | Live queue of a doctor for a day (includes patient name/phone, suggested urgency, reasons) |
| PATCH | `/staff/appointments/{id}/` | `{"urgency"?, "urgency_confirmed"?, "status"?}` |

Status transitions: `booked → checked_in | no_show | cancelled`, `checked_in → in_progress | cancelled`,
`in_progress → completed`. Setting `urgency` marks it confirmed. `no_show`/`cancelled` free the slot.
