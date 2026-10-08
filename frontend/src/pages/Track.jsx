import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { getErrorText } from '../api.js'

export default function Track() {
  const { token } = useParams()
  const [appointment, setAppointment] = useState(null)
  const [notFound, setNotFound] = useState(false)
  const [error, setError] = useState('')

  useEffect(() => {
    function load() {
      api
        .get(`/appointments/${token}/`)
        .then((response) => setAppointment(response.data))
        .catch((err) => {
          if (err.response && err.response.status === 404) {
            setNotFound(true)
          } else {
            setError(getErrorText(err))
          }
        })
    }
    load()
    const timer = setInterval(load, 10000)
    return () => clearInterval(timer)
  }, [token])

  function cancel() {
    if (!window.confirm('Do you want to cancel your booking?')) return
    api
      .post(`/appointments/${token}/cancel/`)
      .then((response) => setAppointment(response.data))
      .catch((err) => setError(getErrorText(err)))
  }

  if (notFound) {
    return (
      <p>
        No active appointment.{' '}
        <Link to="/" className="text-brand-600 underline">
          Book a visit
        </Link>
      </p>
    )
  }

  if (!appointment) {
    return <p className="text-slate-500">{error || 'Loading...'}</p>
  }

  const queue = appointment.queue

  return (
    <div>
      <div className="rounded-xl bg-white p-5 text-center shadow-sm">
        <p className="text-sm text-slate-500">Hello, {appointment.first_name}! Your queue number</p>
        <p className="text-6xl font-bold text-brand-700">{appointment.queue_number}</p>
        <p className="mt-1 capitalize">{appointment.status.replace('_', ' ')}</p>

        {queue.position && (
          <div className="mt-4 grid grid-cols-2 gap-2">
            <div className="rounded-lg bg-slate-50 p-3">
              <div className="text-xs text-slate-500">Position</div>
              <div className="text-xl font-semibold">{queue.position}</div>
            </div>
            <div className="rounded-lg bg-slate-50 p-3">
              <div className="text-xs text-slate-500">Wait</div>
              <div className="text-xl font-semibold">~{queue.wait_minutes} min</div>
            </div>
          </div>
        )}
      </div>

      <div className="mt-4 space-y-1 rounded-xl bg-white p-5 text-sm shadow-sm">
        <p>Clinic: {appointment.clinic}</p>
        <p>
          Doctor: {appointment.doctor} ({appointment.specialty})
        </p>
        <p>Room: {appointment.room}</p>
        <p>Time: {new Date(appointment.slot_start).toLocaleString()}</p>
        <p className="capitalize">
          Urgency: {appointment.urgency} {appointment.urgency_confirmed ? '(confirmed)' : '(not confirmed yet)'}
        </p>
      </div>

      {error && <p className="mt-3 text-red-600">{error}</p>}

      <p className="mt-4 text-xs text-slate-500">This page updates every 10 seconds. Save the link to come back.</p>

      {appointment.status === 'booked' && (
        <button onClick={cancel} className="mt-3 rounded-lg border border-red-300 px-4 py-2 text-red-600">
          Cancel booking
        </button>
      )}
    </div>
  )
}
