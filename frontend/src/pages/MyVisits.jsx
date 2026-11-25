import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api.js'
import { StatusBadge } from '../components/Badge.jsx'
import { useLang } from '../i18n.jsx'
import { getProfile, getTokens, saveProfile } from '../visits.js'

const ACTIVE = ['booked', 'checked_in', 'in_progress']

function VisitCard({ item }) {
  const { t, locale } = useLang()
  return (
    <Link to={`/track/${item.token}`} className="card flex items-center justify-between gap-3 hover:border-brand-200">
      <div>
        <div className="font-medium">
          {item.doctor} <span className="text-sm text-slate-500">({t('sp.' + item.specialty, item.specialty)})</span>
        </div>
        <div className="text-sm text-slate-500">{new Date(item.slot_start).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'short', hour12: false })}</div>
      </div>
      <StatusBadge status={item.status} />
    </Link>
  )
}

export default function MyVisits() {
  const { t } = useLang()
  const [profile, setProfile] = useState(getProfile())
  const [saved, setSaved] = useState(false)
  const [visits, setVisits] = useState([])
  const [loaded, setLoaded] = useState(false)

  useEffect(() => {
    Promise.all(getTokens().map((token) => api.get(`/appointments/${token}/`).then((r) => r.data).catch(() => null))).then(
      (list) => {
        setVisits(list.filter(Boolean))
        setLoaded(true)
      },
    )
  }, [])

  function save(event) {
    event.preventDefault()
    saveProfile(profile)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  const active = visits.filter((item) => ACTIVE.includes(item.status))
  const history = visits.filter((item) => !ACTIVE.includes(item.status))

  return (
    <div>
      <h1 className="text-2xl font-semibold">{t('v.title')}</h1>

      <form onSubmit={save} className="card mt-4">
        <h2 className="mb-3 font-medium">{t('v.profile')}</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <input
            className="input"
            placeholder={t('b.name')}
            value={profile.name}
            onChange={(event) => setProfile({ ...profile, name: event.target.value })}
          />
          <input
            className="input"
            placeholder="+7 701 123 45 67"
            value={profile.phone}
            onChange={(event) => setProfile({ ...profile, phone: event.target.value })}
          />
        </div>
        <div className="mt-3 flex items-center gap-3">
          <button className="btn">{saved ? t('v.saved') : t('v.save')}</button>
          <span className="text-xs text-slate-500">{t('v.hint')}</span>
        </div>
      </form>

      {loaded && visits.length === 0 && <p className="mt-6 text-slate-500">{t('v.empty')}</p>}

      {active.length > 0 && (
        <>
          <h2 className="mb-2 mt-6 font-medium">{t('v.active')}</h2>
          <div className="space-y-3">
            {active.map((item) => (
              <VisitCard key={item.token} item={item} />
            ))}
          </div>
        </>
      )}

      {history.length > 0 && (
        <>
          <h2 className="mb-2 mt-6 font-medium">{t('v.history')}</h2>
          <div className="space-y-3">
            {history.map((item) => (
              <VisitCard key={item.token} item={item} />
            ))}
          </div>
        </>
      )}
    </div>
  )
}
