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
        {clinics[0] && (
          <Link
            to={`/clinics/${clinics[0].slug}/questions`}
            className="mt-5 inline-flex min-h-12 items-center justify-center rounded-xl bg-white px-6 py-3 text-lg font-semibold text-brand-700 shadow transition hover:bg-brand-50"
          >
            {t('home.book')}
          </Link>
        )}
      </section>

      {error && <p className="mt-4 text-red-600">{error}</p>}

      {clinics.map((clinic) => (
        <div key={clinic.id} className="card mt-5">
          <div className="flex items-center justify-between gap-3">
            <div>
              <div className="text-xs font-medium uppercase tracking-wide text-slate-500">{t('home.about')}</div>
              <div className="text-lg font-semibold">{clinic.name}</div>
            </div>
            <Link to={`/clinics/${clinic.slug}/questions`} className="btn shrink-0">
              {t('home.start')}
            </Link>
          </div>
          <dl className="mt-3 grid gap-2 text-sm sm:grid-cols-2">
            <div>
              <dt className="text-slate-500">{t('t.address', 'Адрес')}</dt>
              <dd>{clinic.address}</dd>
            </div>
            {clinic.hours && (
              <div>
                <dt className="text-slate-500">{t('home.hours')}</dt>
                <dd>{clinic.hours}</dd>
              </div>
            )}
            {clinic.phone && (
              <div>
                <dt className="text-slate-500">{t('home.phone')}</dt>
                <dd>
                  <a href={`tel:${clinic.phone.replace(/[^+\d]/g, '')}`} className="text-brand-700 underline">
                    {clinic.phone}
                  </a>
                </dd>
              </div>
            )}
            {clinic.map_url && (
              <div>
                <dt className="text-slate-500">2GIS</dt>
                <dd>
                  <a href={clinic.map_url} target="_blank" rel="noreferrer" className="text-brand-700 underline">
                    {t('home.map')}
                  </a>
                </dd>
              </div>
            )}
          </dl>
        </div>
      ))}

      <Link
        to="/board"
        className="card mt-3 flex items-center justify-between gap-3 text-slate-700 transition hover:bg-slate-50"
      >
        <span className="font-medium">{t('home.board')}</span>
        <span aria-hidden="true" className="text-slate-400">→</span>
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
