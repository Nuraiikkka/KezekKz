import { useEffect, useState } from 'react'
import { useLang } from '../i18n.jsx'

function readTravel() {
  try {
    return Number(localStorage.getItem('travel')) || 20
  } catch {
    return 20
  }
}

export default function LeaveTime({ appointment }) {
  const { t, locale } = useLang()
  const [travel, setTravel] = useState(readTravel)
  const [now, setNow] = useState(() => Date.now())

  useEffect(() => {
    const timer = setInterval(() => setNow(Date.now()), 30000)
    return () => clearInterval(timer)
  }, [])

  const wait = (appointment.queue.wait_minutes || 0) * 60000
  const start = Math.max(new Date(appointment.slot_start).getTime(), now + wait)
  const leave = start - (travel + 5) * 60000
  const leaveNow = leave <= now
  const near = start - now < 24 * 3600000

  useEffect(() => {
    if (leaveNow && 'Notification' in window && Notification.permission === 'granted') {
      new Notification('KezekKz', { body: t('leave.soon') })
    }
  }, [leaveNow, t])

  function changeTravel(value) {
    const number = Math.max(0, Math.min(180, Number(value) || 0))
    setTravel(number)
    try {
      localStorage.setItem('travel', String(number))
    } catch {
      return
    }
  }

  if (!near || !['booked', 'checked_in'].includes(appointment.status)) return null

  return (
    <div className="card mt-4 border-brand-200 bg-gradient-to-br from-brand-50 to-white">
      <div className="text-xs font-medium uppercase tracking-wide text-brand-700">{t('leave.title')}</div>
      <div className="mt-1 text-3xl font-bold text-brand-700">
        {leaveNow ? t('leave.now') : `${t('leave.at')} ${new Date(leave).toLocaleTimeString(locale, { hour: '2-digit', minute: '2-digit', hour12: false })}`}
      </div>
      <label className="mt-2 flex items-center gap-2 text-sm text-slate-600">
        {t('leave.travel')}
        <input
          type="number"
          min="0"
          max="180"
          className="input w-20 py-1"
          value={travel}
          onChange={(event) => changeTravel(event.target.value)}
        />
      </label>
      <p className="mt-2 text-xs text-slate-500">{t('leave.live')}</p>
    </div>
  )
}
