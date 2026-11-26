import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import api, { getErrorText } from '../api.js'
import { UrgencyBadge } from '../components/Badge.jsx'
import Steps from '../components/Steps.jsx'
import { useLang } from '../i18n.jsx'
import { addToken, getProfile, saveProfile } from '../visits.js'

function dayKey(date) {
  return new Date(date).toDateString()
}

export default function Booking() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { t, locale, reasonText } = useLang()
  const intake = useLocation().state
  const profile = getProfile()

  const [specialties, setSpecialties] = useState([])
  const [specialtyCode, setSpecialtyCode] = useState(intake ? intake.specialty.code : '')
  const [slots, setSlots] = useState([])
  const [slotId, setSlotId] = useState(null)
  const [day, setDay] = useState('')
  const [showAll, setShowAll] = useState(intake ? intake.earliest_slot : true)
  const [name, setName] = useState(profile.name)
  const [phone, setPhone] = useState(profile.phone)
  const [error, setError] = useState('')
  const [agreed, setAgreed] = useState(false)
  const [now] = useState(() => new Date())
  const [fast, setFast] = useState(null)

  useEffect(() => {
    api.get(`/clinics/${slug}/specialties/`).then((response) => setSpecialties(response.data))
  }, [slug])

  useEffect(() => {
    if (!specialtyCode) return
    api.get(`/clinics/${slug}/slots/?specialty=${specialtyCode}`).then((response) => {
      setSlots(response.data)
      if (intake.earliest_slot && response.data.length > 0) {
        setSlotId(response.data[0].id)
        setDay(dayKey(response.data[0].start))
      }
    })
  }, [slug, specialtyCode, intake])

  useEffect(() => {
    if (!specialtyCode) return
    api.get(`/clinics/${slug}/recommend/?specialty=${specialtyCode}`).then((response) => setFast(response.data[0] || null))
  }, [slug, specialtyCode])

  if (!intake) {
    return (
      <p>
        {t('b.first')}{' '}
        <Link to={`/clinics/${slug}/questions`} className="text-brand-600 underline">
          {t('b.go')}
        </Link>
      </p>
    )
  }

  const filtered = slots.filter((slot) => {
    const hour = new Date(slot.start).getHours()
    if (showAll || intake.preferred_time === 'no_preference') return true
    if (intake.preferred_time === 'morning') return hour < 13
    return hour >= 13
  })

  const days = []
  filtered.forEach((slot) => {
    if (!days.includes(dayKey(slot.start))) days.push(dayKey(slot.start))
  })
  const currentDay = days.includes(day) ? day : days[0]
  const chosen = specialties.find((item) => item.code === specialtyCode)
  const price = chosen ? chosen.price : null

  const visibleSlots = filtered.filter((slot) => dayKey(slot.start) === currentDay)

  function dayName(key) {
    const date = new Date(key)
    const tomorrow = new Date(now)
    tomorrow.setDate(now.getDate() + 1)
    if (date.toDateString() === now.toDateString()) return t('b.today')
    if (date.toDateString() === tomorrow.toDateString()) return t('b.tomorrow')
    return date.toLocaleDateString(locale, {
      weekday: 'short',
      day: 'numeric',
      month: 'short',
    })
  }

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
      .then((response) => {
        addToken(response.data.token)
        saveProfile({ name, phone })
        navigate(`/track/${response.data.token}`)
      })
      .catch((err) => setError(getErrorText(err)))
  }

  return (
    <div>
      <button type="button" onClick={() => navigate(`/clinics/${slug}/questions`)} className="mb-3 text-sm text-slate-500 underline">
        ← {t('b.back')}
      </button>
      <Steps current={1} />

      {intake.call_103 && (
        <div className="mb-4 rounded-2xl bg-red-600 p-4 font-medium text-white">{t('b.emergency')}</div>
      )}

      <div className="card">
        <div className="text-sm text-slate-500">{t('b.suggested')}</div>
        <div className="text-xl font-semibold">{t('sp.' + intake.specialty.name, intake.specialty.name)}</div>
        <div className="mt-2 flex items-center gap-2 text-sm">
          {t('b.urgency')}: <UrgencyBadge urgency={intake.urgency} />
        </div>
        <ul className="mt-2 list-disc pl-5 text-sm text-slate-600">
          {intake.reasons.map((reason) => (
            <li key={reason}>{reasonText(reason)}</li>
          ))}
        </ul>
        {price !== null && (
          <p className="mt-3 text-sm">
            {t('p.price')}: <b>{price.toLocaleString('ru-RU')} ₸</b>
          </p>
        )}
        <p className="mt-2 text-xs text-slate-500">{t('b.only')}</p>
      </div>

      <form onSubmit={book} className="card mt-4">
        <label className="block text-sm font-medium">{t('b.specialist')}</label>
        <select className="input mt-1" value={specialtyCode} onChange={(event) => changeSpecialty(event.target.value)}>
          {specialties.map((specialty) => (
            <option key={specialty.code} value={specialty.code}>
              {t('sp.' + specialty.name, specialty.name)}
            </option>
          ))}
        </select>

        {fast && (
          <div className="mt-4 rounded-xl border border-brand-200 bg-brand-50 p-3">
            <div className="text-xs font-medium uppercase tracking-wide text-brand-700">⚡ {t('fast.title')}</div>
            <div className="mt-1 flex items-center justify-between gap-3">
              <div className="text-sm">
                <div className="font-medium">
                  {fast.doctor} · {t('t.room')} {fast.room}
                </div>
                <div className="text-slate-600">
                  {t('fast.ready')}: {new Date(fast.slot_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })} (
                  {t('fast.in')} {fast.ready_in_minutes} {t('t.min')})
                </div>
                {fast.real_data && <div className="text-xs text-slate-500">{t('fast.real')}</div>}
              </div>
              <button
                type="button"
                className="btn shrink-0 px-3 py-1.5 text-sm"
                onClick={() => {
                  setShowAll(true)
                  setSlotId(fast.slot_id)
                  setDay(dayKey(fast.slot_start))
                }}
              >
                {t('fast.pick')}
              </button>
            </div>
          </div>
        )}

        <div className="mt-5 flex flex-wrap items-center justify-between gap-2">
          <span className="text-sm font-medium">{t('b.choose')}</span>
          <label className="text-sm text-slate-600">
            <input
              type="checkbox"
              className="mr-1 accent-emerald-700"
              checked={showAll}
              onChange={(event) => setShowAll(event.target.checked)}
            />
            {t('b.all')}
          </label>
        </div>
        {intake.earliest_slot && <p className="text-xs text-amber-700">{t('b.earliest')}</p>}

        <div className="mt-3 flex gap-2 overflow-x-auto pb-1">
          {days.map((key) => (
            <button
              type="button"
              key={key}
              onClick={() => setDay(key)}
              className={`shrink-0 rounded-full px-4 py-1.5 text-sm ${
                key === currentDay ? 'bg-brand-600 text-white' : 'bg-slate-100 text-slate-600'
              }`}
            >
              {dayName(key)}
            </button>
          ))}
        </div>

        <div className="mt-3 grid max-h-64 grid-cols-3 gap-2 overflow-y-auto sm:grid-cols-4">
          {visibleSlots.map((slot) => (
            <button
              type="button"
              key={slot.id}
              onClick={() => setSlotId(slot.id)}
              className={`rounded-xl border p-2 text-sm transition ${
                slotId === slot.id ? 'border-brand-600 bg-brand-600 text-white' : 'border-slate-200 hover:bg-slate-50'
              }`}
            >
              <div className="font-medium">
                {new Date(slot.start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })}
              </div>
              <div className="truncate text-xs opacity-70">{slot.doctor}</div>
            </button>
          ))}
        </div>
        {visibleSlots.length === 0 && <p className="mt-2 text-sm text-slate-500">{t('b.none')}</p>}

        <label className="mt-5 block text-sm font-medium">{t('b.name')}</label>
        <input className="input mt-1" value={name} onChange={(event) => setName(event.target.value)} />

        <label className="mt-3 block text-sm font-medium">{t('b.phone')}</label>
        <input
          className="input mt-1"
          placeholder="+7 701 123 45 67"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
        />

        <label className="mt-4 flex items-start gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            className="mt-1 accent-emerald-700"
            checked={agreed}
            onChange={(event) => setAgreed(event.target.checked)}
          />
          <span>
            {t('b.consent')}
            <span className="block text-xs text-slate-400">{t('b.privacy')}</span>
          </span>
        </label>

        {error && <p className="mt-3 text-red-600">{error}</p>}

        <button disabled={!slotId || !agreed || !name || !phone} className="btn mt-5 w-full">
          {t('b.book')}
        </button>
      </form>
    </div>
  )
}
