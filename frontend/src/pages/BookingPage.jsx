import { useEffect, useMemo, useState } from 'react'
import { Link, Navigate, useLocation, useNavigate, useParams } from 'react-router-dom'
import { parseApiError } from '../api/client.js'
import { createAppointment, getSlots, getSpecialties } from '../api/kezek.js'
import { Button, Card, ErrorBox, Spinner, UrgencyBadge } from '../components/ui.jsx'
import { formatDate, formatTime } from '../utils/format.js'
import { intakeStorageKey } from '../utils/storage.js'

function loadIntake(slug, state) {
  if (state?.intake) return state.intake
  try {
    return JSON.parse(sessionStorage.getItem(intakeStorageKey(slug)))
  } catch {
    return null
  }
}

function groupByDay(slots) {
  const groups = new Map()
  for (const slot of slots) {
    const day = slot.start.slice(0, 10)
    if (!groups.has(day)) groups.set(day, [])
    groups.get(day).push(slot)
  }
  return [...groups.entries()]
}

export default function BookingPage() {
  const { slug } = useParams()
  const location = useLocation()
  const navigate = useNavigate()
  const intake = useMemo(() => loadIntake(slug, location.state), [slug, location.state])

  const [specialties, setSpecialties] = useState([])
  const [specialtyCode, setSpecialtyCode] = useState(intake?.suggested_specialty.code)
  const [onlyPreferredTime, setOnlyPreferredTime] = useState(
    !intake?.offer_earliest_slot && intake?.preferred_time !== 'no_preference',
  )
  const [slots, setSlots] = useState(null)
  const [slotId, setSlotId] = useState(null)
  const [patient, setPatient] = useState({ full_name: '', phone: '' })
  const [errors, setErrors] = useState({})
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  useEffect(() => {
    if (!intake) return
    getSpecialties(slug)
      .then(setSpecialties)
      .catch((e) => setError(parseApiError(e).message))
  }, [slug, intake])

  useEffect(() => {
    if (!intake || !specialtyCode) return
    let cancelled = false
    const params = { specialty: specialtyCode }
    if (onlyPreferredTime && intake.preferred_time !== 'no_preference') params.part_of_day = intake.preferred_time
    getSlots(slug, params)
      .then((data) => {
        if (cancelled) return
        setSlots(data)
        // Urgent case (UC-1 alternate flow): pre-select the earliest free slot.
        if (intake.offer_earliest_slot && data.length) setSlotId(data[0].id)
      })
      .catch((e) => !cancelled && setError(parseApiError(e).message))
    return () => {
      cancelled = true
    }
  }, [slug, intake, specialtyCode, onlyPreferredTime])

  if (!intake) return <Navigate to={`/clinics/${slug}/intake`} replace />

  const submit = async (e) => {
    e.preventDefault()
    setSubmitting(true)
    setError('')
    setErrors({})
    try {
      const appointment = await createAppointment({
        intake_id: intake.id,
        slot_id: slotId,
        specialty_code: specialtyCode,
        patient,
      })
      sessionStorage.removeItem(intakeStorageKey(slug))
      try {
        localStorage.setItem('kezek:lastAppointment', appointment.tracking_token)
      } catch {
        // storage unavailable — the tracking link still works
      }
      navigate(`/track/${appointment.tracking_token}`, { state: { justBooked: true } })
    } catch (err) {
      const { message, fields } = parseApiError(err)
      setErrors(fields)
      setError(message)
      if (fields.slot_id) {
        // Slot was taken meanwhile — refresh the list.
        setSlotId(null)
        getSlots(slug, { specialty: specialtyCode }).then(setSlots).catch(() => {})
      }
    } finally {
      setSubmitting(false)
    }
  }

  const suggested = intake.suggested_specialty

  return (
    <div className="space-y-4">
      {intake.emergency_advice && (
        <div className="rounded-2xl bg-red-600 p-4 text-white" role="alert">
          <div className="font-semibold">Your symptoms may need emergency care.</div>
          <div className="text-sm">
            If you are struggling to breathe or bleeding heavily, call <strong>103</strong> now instead of booking.
          </div>
        </div>
      )}

      <Card>
        <div className="flex items-start justify-between gap-3">
          <div>
            <div className="text-xs uppercase tracking-wide text-slate-500">Suggested specialist</div>
            <div className="text-lg font-semibold">{suggested.name}</div>
          </div>
          <UrgencyBadge urgency={intake.suggested_urgency} />
        </div>
        <ul className="mt-3 list-disc space-y-0.5 pl-5 text-sm text-slate-600">
          {intake.reasons.map((r) => (
            <li key={r}>{r}</li>
          ))}
        </ul>
        <p className="mt-3 text-xs text-slate-500">{intake.disclaimer}</p>
      </Card>

      <form onSubmit={submit} className="space-y-4">
        <Card className="space-y-4">
          <label className="block">
            <span className="text-sm font-medium">Specialist</span>
            <select
              value={specialtyCode}
              onChange={(e) => {
                setSlots(null)
                setSlotId(null)
                setSpecialtyCode(e.target.value)
              }}
              className="mt-1 w-full rounded-xl bg-white p-2.5 ring-1 ring-slate-200"
            >
              {specialties.map((s) => (
                <option key={s.code} value={s.code}>
                  {s.name}
                  {s.code === suggested.code ? ' (suggested)' : ''}
                </option>
              ))}
            </select>
          </label>

          <div>
            <div className="flex items-center justify-between">
              <span className="text-sm font-medium">Choose a time</span>
              {intake.preferred_time !== 'no_preference' && (
                <label className="flex items-center gap-2 text-xs text-slate-600">
                  <input
                    type="checkbox"
                    className="accent-brand-600"
                    checked={onlyPreferredTime}
                    onChange={(e) => {
                      setSlots(null)
                      setSlotId(null)
                      setOnlyPreferredTime(e.target.checked)
                    }}
                  />
                  Only {intake.preferred_time}
                </label>
              )}
            </div>
            {intake.offer_earliest_slot && (
              <p className="mt-1 text-xs text-amber-700">
                Because your case may be urgent, we selected the earliest available time.
              </p>
            )}

            <div className="mt-2 max-h-80 space-y-3 overflow-y-auto">
              {!slots && <Spinner label="Loading free times…" />}
              {slots?.length === 0 && (
                <p className="text-sm text-slate-500">No free times in the next 7 days for this specialist.</p>
              )}
              {slots &&
                groupByDay(slots).map(([day, daySlots]) => (
                  <div key={day}>
                    <div className="mb-1 text-xs font-medium text-slate-500">{formatDate(daySlots[0].start)}</div>
                    <div className="grid grid-cols-3 gap-2 sm:grid-cols-4">
                      {daySlots.map((slot) => (
                        <button
                          type="button"
                          key={slot.id}
                          onClick={() => setSlotId(slot.id)}
                          title={slot.doctor_name}
                          className={`rounded-lg px-2 py-2 text-sm ring-1 transition ${
                            slotId === slot.id
                              ? 'bg-brand-600 text-white ring-brand-600'
                              : 'ring-slate-200 hover:bg-slate-50'
                          }`}
                        >
                          {formatTime(slot.start)}
                          <div className="truncate text-[10px] opacity-75">{slot.doctor_name}</div>
                        </button>
                      ))}
                    </div>
                  </div>
                ))}
            </div>
            {errors.slot_id && <p className="mt-1 text-xs text-red-600">{errors.slot_id}</p>}
          </div>
        </Card>

        <Card className="space-y-3">
          <label className="block">
            <span className="text-sm font-medium">Your name</span>
            <input
              required
              value={patient.full_name}
              onChange={(e) => setPatient({ ...patient, full_name: e.target.value })}
              className="mt-1 w-full rounded-xl p-2.5 ring-1 ring-slate-200 focus:outline-none focus:ring-brand-500"
              autoComplete="name"
            />
            {errors.full_name && <span className="text-xs text-red-600">{errors.full_name}</span>}
          </label>
          <label className="block">
            <span className="text-sm font-medium">Phone</span>
            <input
              required
              type="tel"
              placeholder="+7 701 123 45 67"
              value={patient.phone}
              onChange={(e) => setPatient({ ...patient, phone: e.target.value })}
              className="mt-1 w-full rounded-xl p-2.5 ring-1 ring-slate-200 focus:outline-none focus:ring-brand-500"
              autoComplete="tel"
            />
            {errors.phone && <span className="text-xs text-red-600">{errors.phone}</span>}
          </label>
          <p className="text-xs text-slate-500">We only use your phone to remind you before your turn.</p>
        </Card>

        <ErrorBox message={error} />

        <div className="flex justify-between">
          <Link to={`/clinics/${slug}/intake`} className="px-2 py-2.5 text-sm text-slate-600 underline">
            Change answers
          </Link>
          <Button type="submit" disabled={!slotId || submitting}>
            {submitting ? 'Booking…' : 'Confirm booking'}
          </Button>
        </div>
      </form>
    </div>
  )
}
