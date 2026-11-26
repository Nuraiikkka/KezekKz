import { useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { getErrorText } from '../api.js'
import { StatusBadge, UrgencyBadge } from '../components/Badge.jsx'
import BackLink from '../components/BackLink.jsx'
import LeaveTime from '../components/LeaveTime.jsx'
import Pay from '../components/Pay.jsx'
import PinCard from '../components/PinCard.jsx'
import { useLang } from '../i18n.jsx'
import { addToken } from '../visits.js'

const FLOW = ['booked', 'checked_in', 'in_progress', 'completed']

export default function Track() {
  const { token } = useParams()
  const { t, locale } = useLang()
  const [appointment, setAppointment] = useState(null)
  const [notFound, setNotFound] = useState(false)
  const [error, setError] = useState('')
  const [copied, setCopied] = useState(false)
  const [botName, setBotName] = useState('')
  const [stars, setStars] = useState(0)
  const [comment, setComment] = useState('')

  useEffect(() => {
    function load() {
      api
        .get(`/appointments/${token}/`)
        .then((response) => {
          setAppointment(response.data)
          addToken(token)
        })
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

  const almostTurn = Boolean(
    appointment && appointment.status === 'booked' && appointment.queue.position && appointment.queue.position <= 2,
  )

  useEffect(() => {
    if (almostTurn && 'Notification' in window && Notification.permission === 'granted') {
      new Notification('KezekKz', { body: t('t.soon') })
    }
  }, [almostTurn, t])

  useEffect(() => {
    api.get('/config/').then((response) => setBotName(response.data.telegram_bot || ''))
  }, [])

  useEffect(() => {
    if ('Notification' in window && Notification.permission === 'default') {
      Notification.requestPermission()
    }
  }, [])

  function cancel() {
    if (!window.confirm(t('t.confirm'))) return
    api
      .post(`/appointments/${token}/cancel/`)
      .then((response) => setAppointment(response.data))
      .catch((err) => setError(getErrorText(err)))
  }

  function rate() {
    api
      .post(`/appointments/${token}/rate/`, { rating: stars, comment })
      .then((response) => setAppointment(response.data))
      .catch((err) => setError(getErrorText(err)))
  }

  function post(path, data) {
    api
      .post(`/appointments/${token}/${path}/`, data)
      .then((response) => setAppointment(response.data))
      .catch((err) => setError(getErrorText(err)))
  }

  function confirmVisit() {
    api
      .post(`/appointments/${token}/confirm/`)
      .then((response) => setAppointment(response.data))
      .catch((err) => setError(getErrorText(err)))
  }

  function arrive() {
    api
      .post(`/appointments/${token}/arrive/`)
      .then((response) => setAppointment(response.data))
      .catch((err) => setError(getErrorText(err)))
  }

  function addToCalendar() {
    const start = new Date(appointment.slot_start)
    const end = new Date(start.getTime() + 20 * 60000)
    const format = (date) => date.toISOString().replace(/[-:]/g, '').split('.')[0] + 'Z'
    const text = [
      'BEGIN:VCALENDAR',
      'VERSION:2.0',
      'BEGIN:VEVENT',
      `UID:${token}@kezekkz`,
      `DTSTAMP:${format(new Date())}`,
      `DTSTART:${format(start)}`,
      `DTEND:${format(end)}`,
      `SUMMARY:${appointment.doctor}`,
      `LOCATION:${appointment.clinic}, ${appointment.room}`,
      'END:VEVENT',
      'END:VCALENDAR',
    ].join('\r\n')
    const link = document.createElement('a')
    link.href = URL.createObjectURL(new Blob([text], { type: 'text/calendar' }))
    link.download = 'visit.ics'
    link.click()
  }

  function copyLink() {
    navigator.clipboard.writeText(window.location.href).then(() => {
      setCopied(true)
      setTimeout(() => setCopied(false), 2000)
    })
  }

  if (notFound) {
    return (
      <p>
        {t('t.none')}{' '}
        <Link to="/" className="text-brand-600 underline">
          {t('t.book')}
        </Link>
      </p>
    )
  }

  if (!appointment) {
    return <p className="text-slate-500">{error || t('loading')}</p>
  }

  const queue = appointment.queue
  const step = FLOW.indexOf(appointment.status)
  const finished = ['cancelled', 'no_show'].includes(appointment.status)

  return (
    <div>
      <BackLink to="/my" />
      {almostTurn && (
        <div className="mb-4 rounded-2xl bg-amber-100 p-4 font-medium text-amber-900">
          {t('t.soon')} {appointment.room}.
        </div>
      )}

      <div className="card text-center">
        <p className="text-sm text-slate-500">
          {t('t.hello')}, {appointment.first_name}! {t('t.number')}
        </p>
        <p className="text-7xl font-bold text-brand-700">{appointment.queue_number}</p>
        <div className="mt-2 flex justify-center gap-2">
          <StatusBadge status={appointment.status} />
          <UrgencyBadge urgency={appointment.urgency} />
        </div>

        {!finished && (
          <div className="mt-5 flex items-center">
            {FLOW.map((name, index) => (
              <div key={name} className="flex flex-1 items-center last:flex-none">
                <div
                  className={`h-3 w-3 rounded-full ${index <= step ? 'bg-brand-600' : 'bg-slate-200'} ${
                    index === step ? 'ring-4 ring-brand-100' : ''
                  }`}
                />
                {index < FLOW.length - 1 && <div className={`h-0.5 flex-1 ${index < step ? 'bg-brand-600' : 'bg-slate-200'}`} />}
              </div>
            ))}
          </div>
        )}

        {queue.position && (
          <div className="mt-5 grid grid-cols-2 gap-3">
            <div className="rounded-xl bg-brand-50 p-3">
              <div className="text-xs text-slate-500">{t('t.position')}</div>
              <div className="text-2xl font-semibold">{queue.position}</div>
            </div>
            <div className="rounded-xl bg-brand-50 p-3">
              <div className="text-xs text-slate-500">{t('t.wait')}</div>
              <div className="text-2xl font-semibold">
                ~{queue.wait_minutes} {t('t.min')}
              </div>
            </div>
          </div>
        )}
      </div>

      {queue.visit_minutes && (
        <p className="mt-3 text-center text-xs text-slate-500">
          {queue.real_data ? t('t.real') : t('t.default')}: ~{queue.visit_minutes} {t('t.min')}
        </p>
      )}

      <div className="card mt-4 space-y-2 text-sm">
        <p>
          <span className="text-slate-500">{t('t.clinic')}:</span> {appointment.clinic}
        </p>
        <p>
          <span className="text-slate-500">{t('t.doctor')}:</span> {appointment.doctor} (
          {t('sp.' + appointment.specialty, appointment.specialty)})
        </p>
        <p>
          <span className="text-slate-500">{t('t.room')}:</span> {appointment.room}
        </p>
        <p>
          <span className="text-slate-500">{t('t.time')}:</span> {new Date(appointment.slot_start).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'short', hour12: false })}
        </p>
        <p>
          <span className="text-slate-500">{t('p.priceshort')}:</span>{' '}
          {appointment.billed ? `${appointment.price.toLocaleString('ru-RU')} ₸` : t('p.doctorpriceshort')}
          {appointment.payment && appointment.payment.status === 'paid' && (
            <span className="ml-2 text-brand-700">✓ {t('p.paidshort')}</span>
          )}
        </p>
        <p>
          <span className="text-slate-500">{t('b.urgency')}:</span> {t('urgency.' + appointment.urgency)} (
          {appointment.urgency_confirmed ? t('t.confirmed') : t('t.notconfirmed')})
        </p>
      </div>

      <LeaveTime appointment={appointment} />

      {['booked', 'checked_in'].includes(appointment.status) && (
        <div className="card mt-4 text-sm">
          <h2 className="mb-1 font-medium">{t('prep.title')}</h2>
          <p className="text-slate-600">{t('prep.' + appointment.specialty_code, t('prep.generic'))}</p>
          <p className="mt-1 text-slate-500">{t('prep.generic')}</p>
          <a
            href={`https://2gis.kz/search/${encodeURIComponent(appointment.clinic_address || appointment.clinic)}`}
            target="_blank"
            rel="noreferrer"
            className="btn-light mt-3"
          >
            📍 {t('addr.open')}
          </a>
        </div>
      )}

      {appointment.status === 'completed' && (
        <div className="card mt-4 text-center">
          <p className="font-medium">{appointment.rating ? t('t.thanks') : t('t.rate')}</p>
          <div className="mt-2 flex justify-center gap-1 text-3xl">
            {[1, 2, 3, 4, 5].map((value) => (
              <button
                key={value}
                disabled={Boolean(appointment.rating)}
                onClick={() => setStars(value)}
                className={value <= (appointment.rating || stars) ? 'text-amber-400' : 'text-slate-300'}
              >
                ★
              </button>
            ))}
          </div>
          {!appointment.rating && stars > 0 && (
            <div className="mt-3 text-left">
              <textarea
                className="input"
                rows={2}
                maxLength={500}
                placeholder={t('t.comment')}
                value={comment}
                onChange={(event) => setComment(event.target.value)}
              />
              <button onClick={rate} className="btn mt-2">
                {t('t.send')}
              </button>
            </div>
          )}
          {appointment.rating_comment && <p className="mt-2 text-sm text-slate-600">“{appointment.rating_comment}”</p>}
        </div>
      )}

      {appointment.status === 'completed' && appointment.billed && <Pay appointment={appointment} onChange={setAppointment} />}
      {['checked_in', 'in_progress', 'completed'].includes(appointment.status) && !appointment.billed && (
        <div className="card mt-4 text-sm text-slate-600">{t('p.afterprice')}</div>
      )}
      {appointment.status === 'booked' && <p className="mt-4 text-center text-xs text-slate-500">{t('p.when')}</p>}

      {appointment.status !== 'cancelled' && <PinCard appointment={appointment} token={token} />}

      {appointment.offer && (
        <div className="card mt-4 border-brand-200 bg-brand-50">
          <p className="font-medium">{t('e.offer')}</p>
          <p className="mt-1 text-sm">
            {new Date(appointment.offer.slot_start).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'short', hour12: false })} ·{' '}
            {appointment.offer.doctor} · {t('t.room')} {appointment.offer.room}
          </p>
          <p className="text-xs text-slate-500">
            {t('e.left')}: {appointment.offer.minutes_left}
          </p>
          <div className="mt-3 flex gap-2">
            <button onClick={() => post('offer/accept')} className="btn">
              {t('e.accept')}
            </button>
            <button onClick={() => post('offer/decline')} className="btn-light">
              {t('e.decline')}
            </button>
          </div>
        </div>
      )}

      {appointment.status === 'booked' && !appointment.offer && (
        <div className="card mt-4 text-sm">
          {appointment.wants_earlier ? (
            <div className="flex items-center justify-between gap-3">
              <span className="text-slate-600">{t('e.on')}</span>
              <button onClick={() => post('earlier', { wants: false })} className="btn-light shrink-0">
                {t('e.off')}
              </button>
            </div>
          ) : (
            <button onClick={() => post('earlier', { wants: true })} className="btn-light w-full">
              {t('e.ask')}
            </button>
          )}
        </div>
      )}

      {botName && ['booked', 'checked_in'].includes(appointment.status) && (
        <div className="card mt-4 text-sm">
          {appointment.telegram_connected ? (
            <p className="text-brand-700">✓ {t('tg.on')}</p>
          ) : (
            <div className="flex items-center justify-between gap-3">
              <span className="text-slate-600">{t('tg.hint')}</span>
              <a
                href={`https://t.me/${botName}?start=${token}`}
                target="_blank"
                rel="noreferrer"
                className="btn shrink-0"
              >
                {t('tg.connect')}
              </a>
            </div>
          )}
        </div>
      )}

      {appointment.status === 'booked' && appointment.patient_confirmed && (
        <p className="mt-3 text-sm text-brand-700">✓ {t('t.confirmed2')}</p>
      )}

      {error && <p className="mt-3 text-red-600">{error}</p>}

      <p className="mt-4 text-xs text-slate-500">{t('t.refresh')}</p>

      <div className="mt-3 flex flex-wrap gap-2">
        <button onClick={copyLink} className="btn-light">
          {copied ? t('t.copied') : t('t.copy')}
        </button>
        {appointment.status === 'booked' && !appointment.patient_confirmed && (
          <button onClick={confirmVisit} className="btn">
            {t('t.confirmcome')}
          </button>
        )}
        {appointment.status === 'booked' && (
          <button onClick={arrive} className="btn">
            {t('t.arrive')}
          </button>
        )}
        {!finished && appointment.status !== 'completed' && (
          <button onClick={addToCalendar} className="btn-light">
            {t('t.calendar')}
          </button>
        )}
        {appointment.status === 'booked' && (
          <button onClick={cancel} className="btn-light border-red-200 text-red-600">
            {t('t.cancel')}
          </button>
        )}
      </div>
    </div>
  )
}
