import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import api, { getErrorText } from '../api.js'

function showTime(date) {
  return new Date(date).toLocaleString([], { weekday: 'short', day: 'numeric', hour: '2-digit', minute: '2-digit' })
}

export default function Booking() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const intake = useLocation().state

  const [specialties, setSpecialties] = useState([])
  const [specialtyCode, setSpecialtyCode] = useState(intake ? intake.specialty.code : '')
  const [slots, setSlots] = useState([])
  const [slotId, setSlotId] = useState(null)
  const [showAll, setShowAll] = useState(intake ? intake.earliest_slot : true)
  const [name, setName] = useState('')
  const [phone, setPhone] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    api.get(`/clinics/${slug}/specialties/`).then((response) => setSpecialties(response.data))
  }, [slug])

  useEffect(() => {
    if (!specialtyCode) return
    api.get(`/clinics/${slug}/slots/?specialty=${specialtyCode}`).then((response) => {
      setSlots(response.data)
      if (intake.earliest_slot && response.data.length > 0) {
        setSlotId(response.data[0].id)
      }
    })
  }, [slug, specialtyCode, intake])

  if (!intake) {
    return (
      <p>
        Please answer the questions first.{' '}
        <Link to={`/clinics/${slug}/questions`} className="text-brand-600 underline">
          Go to questions
        </Link>
      </p>
    )
  }

  const visibleSlots = slots.filter((slot) => {
    const hour = new Date(slot.start).getHours()
    if (showAll || intake.preferred_time === 'no_preference') return true
    if (intake.preferred_time === 'morning') return hour < 13
    return hour >= 13
  })

  function changeSpecialty(code) {
    setSlotId(null)
    setSpecialtyCode(code)
  }

  function book(event) {
    event.preventDefault()
    setError('')
    const data = {
      intake_id: intake.id,
      slot_id: slotId,
      specialty_code: specialtyCode,
      patient: { full_name: name, phone: phone },
    }
    api
      .post('/appointments/', data)
      .then((response) => navigate(`/track/${response.data.token}`))
      .catch((err) => setError(getErrorText(err)))
  }

  return (
    <div>
      {intake.call_103 && (
        <div className="mb-4 rounded-xl bg-red-600 p-4 text-white">
          Your symptoms may be an emergency. Please call 103 now.
        </div>
      )}

      <div className="rounded-xl bg-white p-5 shadow-sm">
        <div className="text-sm text-slate-500">Suggested specialist</div>
        <div className="text-lg font-semibold">{intake.specialty.name}</div>
        <div className="mt-1">
          Urgency: <b className="capitalize">{intake.urgency}</b>
        </div>
        <ul className="mt-2 list-disc pl-5 text-sm text-slate-600">
          {intake.reasons.map((reason) => (
            <li key={reason}>{reason}</li>
          ))}
        </ul>
        <p className="mt-2 text-xs text-slate-500">This is only a suggestion. Clinic staff will confirm it.</p>
      </div>

      <form onSubmit={book} className="mt-4 rounded-xl bg-white p-5 shadow-sm">
        <label className="block text-sm font-medium">Specialist</label>
        <select
          className="mt-1 w-full rounded-lg border p-2"
          value={specialtyCode}
          onChange={(event) => changeSpecialty(event.target.value)}
        >
          {specialties.map((specialty) => (
            <option key={specialty.code} value={specialty.code}>
              {specialty.name}
            </option>
          ))}
        </select>

        <div className="mt-4 flex items-center justify-between">
          <span className="text-sm font-medium">Choose a time</span>
          <label className="text-sm text-slate-600">
            <input type="checkbox" checked={showAll} onChange={(event) => setShowAll(event.target.checked)} /> Show
            all times
          </label>
        </div>
        {intake.earliest_slot && (
          <p className="text-xs text-amber-700">Your case may be urgent, so we chose the earliest time.</p>
        )}

        <div className="mt-2 grid max-h-72 grid-cols-3 gap-2 overflow-y-auto">
          {visibleSlots.map((slot) => (
            <button
              type="button"
              key={slot.id}
              onClick={() => setSlotId(slot.id)}
              className={`rounded-lg border p-2 text-sm ${slotId === slot.id ? 'bg-brand-600 text-white' : ''}`}
            >
              {showTime(slot.start)}
              <div className="truncate text-xs opacity-70">{slot.doctor}</div>
            </button>
          ))}
        </div>
        {visibleSlots.length === 0 && <p className="text-sm text-slate-500">No free times.</p>}

        <label className="mt-4 block text-sm font-medium">Your name</label>
        <input className="mt-1 w-full rounded-lg border p-2" value={name} onChange={(event) => setName(event.target.value)} />

        <label className="mt-3 block text-sm font-medium">Phone</label>
        <input
          className="mt-1 w-full rounded-lg border p-2"
          placeholder="+7 701 123 45 67"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
        />

        {error && <p className="mt-3 text-red-600">{error}</p>}

        <button disabled={!slotId} className="mt-4 w-full rounded-lg bg-brand-600 py-2 text-white disabled:opacity-50">
          Book
        </button>
      </form>
    </div>
  )
}
