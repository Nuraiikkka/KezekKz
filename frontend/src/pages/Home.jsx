import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { getErrorText } from '../api.js'
import { useLang } from '../i18n.jsx'
import { getTokens } from '../visits.js'

export default function Home() {
  const { t } = useLang()
  const [clinics, setClinics] = useState([])
  const [activeToken, setActiveToken] = useState('')
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get('/clinics/')
      .then((response) => setClinics(response.data))
      .catch((err) => setError(getErrorText(err)))

    const tokens = getTokens().slice(0, 5)
    Promise.all(tokens.map((token) => api.get(`/appointments/${token}/`).then((r) => r.data).catch(() => null))).then(
      (list) => {
        const active = list.find((item) => item && ['booked', 'checked_in', 'in_progress'].includes(item.status))
        if (active) setActiveToken(active.token)
      },
    )
  }, [])

  const steps = [
    ['1', t('home.step1'), t('home.step1text')],
    ['2', t('home.step2'), t('home.step2text')],
    ['3', t('home.step3'), t('home.step3text')],
  ]

  return (
    <div>
      {activeToken && (
        <div className="mb-4 flex items-center justify-between rounded-2xl bg-amber-100 p-4 text-amber-900">
          <span>{t('home.active')}</span>
          <Link to={`/track/${activeToken}`} className="rounded-lg bg-amber-600 px-3 py-1 text-sm text-white">
            {t('home.open')}
          </Link>
        </div>
      )}

      <section className="rounded-3xl bg-gradient-to-br from-brand-700 to-brand-500 p-7 text-white shadow-lg">
        <h1 className="text-3xl font-bold leading-tight">{t('home.title')}</h1>
        <p className="mt-3 max-w-xl text-brand-50">{t('home.text')}</p>
      </section>

      {error && <p className="mt-4 text-red-600">{error}</p>}

      {clinics.map((clinic) => (
        <div key={clinic.id} className="card mt-5 flex items-center justify-between gap-3">
          <div>
            <div className="text-lg font-semibold">{clinic.name}</div>
            <div className="text-sm text-slate-500">{clinic.address}</div>
          </div>
          <Link to={`/clinics/${clinic.slug}/questions`} className="btn shrink-0">
            {t('home.start')}
          </Link>
        </div>
      ))}

      <Link to="/board" className="btn-light mt-3 w-full">
        {t('home.board')}
      </Link>

      <h2 className="mb-3 mt-8 text-lg font-semibold">{t('home.how')}</h2>
      <div className="grid gap-3 sm:grid-cols-3">
        {steps.map(([number, title, text]) => (
          <div key={number} className="card">
            <div className="mb-2 flex h-8 w-8 items-center justify-center rounded-full bg-brand-100 font-semibold text-brand-700">
              {number}
            </div>
            <div className="font-medium">{title}</div>
            <div className="text-sm text-slate-500">{text}</div>
          </div>
        ))}
      </div>
    </div>
  )
}
