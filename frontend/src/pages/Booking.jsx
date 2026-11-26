import { useEffect, useState } from 'react'
import { Link, useLocation, useNavigate, useParams } from 'react-router-dom'
import api, { getErrorText } from '../api.js'
import { UrgencyBadge } from '../components/Badge.jsx'
import EmptyState from '../components/EmptyState.jsx'
import NeedsForm from '../components/NeedsForm.jsx'
import Steps from '../components/Steps.jsx'
import { useLang } from '../i18n.jsx'
import { addToken, getProfile, saveProfile } from '../visits.js'

function savedIntake(slug) {
  try {
    return JSON.parse(sessionStorage.getItem('kezek-intake-' + slug))
  } catch {
    return null
  }
}

function patientToken() {
  try {
    return localStorage.getItem('patientToken') || ''
  } catch {
    return ''
  }
}

function validPhone(value) {
  const digits = value.replace(/[\s()-]/g, '')
  return /^(\+7|8)\d{10}$/.test(digits)
}

function dayKey(date) {
  return new Date(date).toDateString()
}

export default function Booking() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { t, locale, reasonText } = useLang()
  const location = useLocation()
  const intake = location.state || savedIntake(slug)
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
  const [now] = useState(() => new Date())
  const [fast, setFast] = useState(null)
  const [family, setFamily] = useState([])
  const [loggedIn, setLoggedIn] = useState(false)
  const [memberId, setMemberId] = useState('')
  const [needs, setNeeds] = useState({})

  useEffect(() => {
    api.get(`/clinics/${slug}/specialties/`).then((response) => setSpecialties(response.data))
  }, [slug])

  useEffect(() => {
    const token = patientToken()
    if (!token) return
    api
      .get('/patient/me/', { headers: { 'X-Patient-Token': token } })
      .then((response) => {
        setLoggedIn(true)
        setFamily(response.data.family || [])
        const { full_name: fullName, phone: ownPhone } = response.data.profile
        setName((current) => current || fullName)
        setPhone((current) => ownPhone || current)
      })
      .catch(() => setLoggedIn(false))
  }, [])

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
    return <EmptyState title={t('nf.lost')} text={t('nf.losttext')} to={`/clinics/${slug}/questions`} action={t('nf.again')} />
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

  const visibleSlots = filtered.filter((slot) => dayKey(slot.start) === currentDay)
  const hasEarlier = !showAll && slots.length > 0 && filtered.length > 0 && new Date(slots[0].start) < new Date(filtered[0].start)
  const nameOk = name.trim().length >= 2
  const phoneOk = validPhone(phone)

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
    if (!nameOk) return setError(t('b.badname'))
    if (!phoneOk) return setError(t('b.badphone'))
    const data = {
      intake_id: intake.id,
      slot_id: slotId,
      specialty_code: specialtyCode,
      patient: { full_name: name.trim(), phone: phone.replace(/[\s()-]/g, '') },
      needs,
    }
    if (memberId) data.family_member_id = Number(memberId)
    api
      .post('/appointments/', data, { headers: { 'X-Patient-Token': patientToken() } })
      .then((response) => {
        addToken(response.data.token)
        saveProfile({ name: name.trim(), phone })
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
        <p className="mt-3 text-sm text-slate-600">{t('p.doctorprice')}</p>
        <p className="mt-2 text-xs text-slate-500">{t('b.only')}</p>
      </div>

      <form onSubmit={book}>
      <div className="card mt-4">
        <h2 className="mb-3 text-lg font-semibold">{t('b.sec_time')}</h2>
        <label htmlFor="specialist" className="block text-sm font-medium">{t('b.specialist')}</label>
        <select id="specialist" className="input mt-1" value={specialtyCode} onChange={(event) => changeSpecialty(event.target.value)}>
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
        {hasEarlier && (
          <p className="mt-2 text-xs text-amber-700">
            {t('b.earlier')}{' '}
            <button type="button" onClick={() => setShowAll(true)} className="underline">
              {t('b.all')}
            </button>
          </p>
        )}

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
      </div>

      <div className="card mt-4">
        <h2 className="mb-3 text-lg font-semibold">{t('fam.for')}</h2>
        {loggedIn ? (
          <select
            aria-label={t('fam.for')}
            className="input"
            value={memberId}
            onChange={(event) => setMemberId(event.target.value)}
          >
            <option value="">{t('fam.me')}</option>
            {family.map((member) => (
              <option key={member.id} value={member.id}>
                {member.full_name} · {t('rel.' + member.relation)}, {member.age} {t('fam.years')}
              </option>
            ))}
          </select>
        ) : (
          <p className="text-sm text-slate-600">
            {t('fam.login')}{' '}
            <Link to="/my" className="text-brand-700 underline">
              {t('nav.visits')}
            </Link>
          </p>
        )}
      </div>

      <NeedsForm value={needs} onChange={setNeeds} />

      <div className="card mt-4">
        <h2 className="mb-3 text-lg font-semibold">{t('b.sec_contact')}</h2>
        <label htmlFor="patient-name" className="block text-sm font-medium">{t('b.name')}</label>
        <input
          id="patient-name"
          className="input mt-1"
          autoComplete="name"
          value={name}
          onChange={(event) => setName(event.target.value)}
        />

        <label htmlFor="patient-phone" className="mt-3 block text-sm font-medium">{t('b.phone')}</label>
        <input
          id="patient-phone"
          className="input mt-1"
          type="tel"
          autoComplete="tel"
          placeholder="+7 701 123 45 67"
          value={phone}
          onChange={(event) => setPhone(event.target.value)}
        />

        {error && <p role="alert" className="mt-3 text-red-600">{error}</p>}

        <button disabled={!slotId || !nameOk || !phoneOk} className="btn mt-5 w-full">
          {t('b.book')}
        </button>
      </div>
      </form>
    </div>
  )
}
