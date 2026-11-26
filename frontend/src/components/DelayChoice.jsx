import { useEffect, useState } from 'react'
import api, { getErrorText } from '../api.js'
import { useLang } from '../i18n.jsx'

function storeKey(token, delay) {
  return `kezek-wait-${token}-${delay}`
}

export default function DelayChoice({ appointment, token, onMoved }) {
  const { t, locale } = useLang()
  const delay = appointment.doctor_delay
  const [mode, setMode] = useState('')
  const [waiting, setWaiting] = useState(() => {
    try {
      return localStorage.getItem(storeKey(token, delay)) === '1'
    } catch {
      return false
    }
  })
  const [slots, setSlots] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    if (!mode) return
    api
      .get(`/clinics/${appointment.clinic_slug}/slots/?specialty=${appointment.specialty_code}`)
      .then((response) => setSlots(response.data))
      .catch((err) => setError(getErrorText(err)))
  }, [mode, appointment.clinic_slug, appointment.specialty_code])

  if (appointment.status !== 'booked' || !delay) return null

  function wait() {
    setWaiting(true)
    setMode('')
    try {
      localStorage.setItem(storeKey(token, delay), '1')
    } catch {
      return
    }
  }

  function pick(slot) {
    setError('')
    api
      .post(`/appointments/${token}/move/`, { slot_id: slot.id })
      .then((response) => {
        setMode('')
        onMoved(response.data)
      })
      .catch((err) => setError(getErrorText(err)))
  }

  const visible = slots
    .filter((slot) => (mode === 'move' ? slot.doctor === appointment.doctor : slot.doctor !== appointment.doctor))
    .slice(0, 8)

  return (
    <div role="region" aria-label={t('delay.title')} className="card mt-4 border-amber-200 bg-amber-50">
      <p className="font-medium text-amber-900">
        ⏱ {t('delay.title')}: {delay} {t('delay.min')}
      </p>

      {waiting && !mode ? (
        <p className="mt-2 text-sm text-slate-700">{t('delay.waiting')}</p>
      ) : (
        <p className="mt-1 text-sm text-slate-700">{t('delay.ask')}</p>
      )}

      <div className="mt-3 flex flex-wrap gap-2">
        {!waiting && (
          <button type="button" onClick={wait} className="btn-light">
            {t('delay.wait')}
          </button>
        )}
        <button type="button" onClick={() => setMode(mode === 'move' ? '' : 'move')} className={mode === 'move' ? 'btn' : 'btn-light'}>
          {t('delay.move')}
        </button>
        <button type="button" onClick={() => setMode(mode === 'switch' ? '' : 'switch')} className={mode === 'switch' ? 'btn' : 'btn-light'}>
          {t('delay.switch')}
        </button>
      </div>

      {mode && (
        <div className="mt-3">
          <p className="text-sm font-medium">
            {t('delay.pick')} · {mode === 'move' ? t('delay.same') : t('delay.other')}
          </p>
          {visible.length === 0 && <p className="mt-2 text-sm text-slate-500">{t('delay.none')}</p>}
          <div className="mt-2 grid grid-cols-2 gap-2 sm:grid-cols-4">
            {visible.map((slot) => (
              <button
                type="button"
                key={slot.id}
                onClick={() => pick(slot)}
                className="rounded-xl border border-slate-200 bg-white p-2 text-sm transition hover:bg-slate-50"
              >
                <div className="font-medium">
                  {new Date(slot.start).toLocaleString(locale, { weekday: 'short', hour: '2-digit', minute: '2-digit', hour12: false })}
                </div>
                {mode === 'switch' && <div className="truncate text-xs text-slate-500">{slot.doctor}</div>}
              </button>
            ))}
          </div>
        </div>
      )}
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  )
}
