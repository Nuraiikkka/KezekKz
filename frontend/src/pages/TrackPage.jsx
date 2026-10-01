import { useCallback, useEffect, useState } from 'react'
import { useLocation, useParams } from 'react-router-dom'
import { parseApiError } from '../api/client.js'
import { cancelAppointment, trackAppointment } from '../api/kezek.js'
import { Button, Card, ErrorBox, Spinner, UrgencyBadge } from '../components/ui.jsx'
import { formatDate, formatTime } from '../utils/format.js'

const REFRESH_MS = 30_000

const STATUS_TEXT = {
  booked: 'Booked',
  checked_in: 'Checked in — please stay nearby',
  in_progress: "It's your turn — please go in",
  completed: 'Visit completed',
  no_show: 'Marked as missed',
  cancelled: 'Cancelled',
}

function formatWait(minutes) {
  if (minutes == null) return '—'
  if (minutes < 60) return `~${minutes} min`
  const h = Math.floor(minutes / 60)
  const m = minutes % 60
  if (h >= 24) return `~${Math.round(h / 24)} day(s)`
  return `~${h} h ${m ? `${m} min` : ''}`
}

export default function TrackPage() {
  const { token } = useParams()
  const location = useLocation()
  const [appt, setAppt] = useState(null)
  const [error, setError] = useState('')
  const [updatedAt, setUpdatedAt] = useState(null)
  const [cancelling, setCancelling] = useState(false)
  const [copied, setCopied] = useState(false)

  const load = useCallback(() => {
    trackAppointment(token)
      .then((data) => {
        setAppt(data)
        setError('')
        setUpdatedAt(new Date())
      })
      .catch((e) =>
        setError(e?.response?.status === 404 ? 'Appointment not found. Check your link.' : parseApiError(e).message),
      )
  }, [token])

  useEffect(() => {
    load()
    const id = setInterval(load, REFRESH_MS)
    return () => clearInterval(id)
  }, [load])

  const cancel = async () => {
    if (!window.confirm('Cancel this appointment? The time will be offered to other patients.')) return
    setCancelling(true)
    try {
      setAppt(await cancelAppointment(token))
    } catch (e) {
      setError(parseApiError(e).message)
    } finally {
      setCancelling(false)
    }
  }

  const copyLink = async () => {
    try {
      await navigator.clipboard.writeText(window.location.href)
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    } catch {
      // clipboard not available
    }
  }

  if (!appt) return error ? <ErrorBox message={error} onRetry={load} /> : <Spinner />

  const q = appt.queue
  const active = q.position !== null

  return (
    <div className="space-y-4">
      {location.state?.justBooked && (
        <div className="rounded-2xl bg-brand-50 p-4 text-sm text-brand-700 ring-1 ring-brand-100">
          You're booked, {appt.patient_first_name}! Save this page — it shows your live place in the queue.
        </div>
      )}

      <Card className="text-center">
        <div className="text-xs uppercase tracking-wide text-slate-500">Your queue number</div>
        <div className="text-6xl font-bold text-brand-700">{appt.queue_number}</div>
        <div className="mt-1 text-sm font-medium">{STATUS_TEXT[appt.status]}</div>

        {active && (
          <div className="mt-5 grid grid-cols-3 gap-2">
            <div className="rounded-xl bg-slate-50 p-3">
              <div className="text-xs text-slate-500">Position</div>
              <div className="text-xl font-semibold">{q.position === 0 ? 'Now' : q.position}</div>
            </div>
            <div className="rounded-xl bg-slate-50 p-3">
              <div className="text-xs text-slate-500">Est. wait</div>
              <div className="text-xl font-semibold">{formatWait(q.estimated_wait_minutes)}</div>
            </div>
            <div className="rounded-xl bg-slate-50 p-3">
              <div className="text-xs text-slate-500">Est. start</div>
              <div className="text-xl font-semibold">{q.estimated_start ? formatTime(q.estimated_start) : '—'}</div>
            </div>
          </div>
        )}
        {active && q.doctor_delay_minutes > 0 && (
          <p className="mt-3 text-sm text-amber-700">The doctor is running about {q.doctor_delay_minutes} min late.</p>
        )}
      </Card>

      <Card className="space-y-2 text-sm">
        <Row label="Clinic" value={appt.clinic_name} />
        <Row label="Doctor" value={`${appt.doctor_name} · ${appt.specialty}`} />
        {appt.room && <Row label="Room" value={appt.room} />}
        <Row label="Booked time" value={`${formatDate(appt.slot_start)}, ${formatTime(appt.slot_start)}`} />
        <Row
          label="Urgency"
          value={
            <span className="flex items-center gap-2">
              <UrgencyBadge urgency={appt.urgency} />
              {!appt.urgency_confirmed && <span className="text-xs text-slate-500">awaiting staff confirmation</span>}
            </span>
          }
        />
      </Card>

      <ErrorBox message={error} />

      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className="text-xs text-slate-500">
          Updates automatically{updatedAt && ` · last ${updatedAt.toLocaleTimeString()}`}
        </span>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={copyLink}>
            {copied ? 'Copied!' : 'Copy link'}
          </Button>
          {appt.status === 'booked' && (
            <Button variant="danger" onClick={cancel} disabled={cancelling}>
              {cancelling ? 'Cancelling…' : 'Cancel'}
            </Button>
          )}
        </div>
      </div>
    </div>
  )
}

function Row({ label, value }) {
  return (
    <div className="flex justify-between gap-4">
      <span className="text-slate-500">{label}</span>
      <span className="text-right font-medium">{value}</span>
    </div>
  )
}
