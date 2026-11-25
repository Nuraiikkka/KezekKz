import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { getErrorText } from '../api.js'
import { useLang } from '../i18n.jsx'

export default function Stats() {
  const { t } = useLang()
  const [days, setDays] = useState(30)
  const [data, setData] = useState(null)
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get(`/staff/stats/?days=${days}`, { headers: { Authorization: `Token ${localStorage.getItem('staffToken')}` } })
      .then((response) => setData(response.data))
      .catch((err) => setError(err.response && err.response.status === 401 ? '401' : getErrorText(err)))
  }, [days])

  if (error === '401') {
    return (
      <Link to="/staff" className="text-brand-600 underline">
        {t('s.login')}
      </Link>
    )
  }
  if (!data) return <p className="text-slate-500">{error || t('loading')}</p>

  const maxHour = Math.max(1, ...data.by_hour.map((item) => item.count))

  const cards = [
    [t('st.visits'), data.total],
    [t('st.revenue'), `${data.revenue.toLocaleString('ru-RU')} ₸`],
    [t('st.done'), data.completed],
    [t('st.noshowrate'), `${data.no_show_rate}%`],
    [t('st.cancel'), data.cancelled],
    [t('st.rating'), data.avg_rating ? `${data.avg_rating} ★` : '—'],
    [t('st.delay'), `${data.avg_delay_minutes} ${t('t.min')}`],
  ]

  return (
    <div>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <h1 className="text-2xl font-semibold">{t('st.title')}</h1>
        <Link to="/staff" className="text-sm text-slate-500 underline">
          {t('st.back')}
        </Link>
      </div>

      <div className="mt-3 flex items-center gap-2 text-sm">
        <span className="text-slate-500">{t('st.days')}:</span>
        {[7, 30, 90].map((value) => (
          <button
            key={value}
            onClick={() => setDays(value)}
            className={`rounded-full px-3 py-1 ${days === value ? 'bg-brand-600 text-white' : 'bg-slate-100'}`}
          >
            {value}
          </button>
        ))}
      </div>

      <div className="mt-4 grid grid-cols-2 gap-3 sm:grid-cols-3">
        {cards.map(([label, value]) => (
          <div key={label} className="card text-center">
            <div className="text-2xl font-bold text-brand-700">{value}</div>
            <div className="text-xs text-slate-500">{label}</div>
          </div>
        ))}
      </div>

      <div className="card mt-4">
        <h2 className="mb-3 font-medium">{t('st.hours')}</h2>
        <div className="flex h-36 items-end gap-1">
          {data.by_hour.map((item) => (
            <div key={item.hour} className="flex flex-1 flex-col items-center justify-end gap-1">
              <span className="text-xs text-slate-500">{item.count}</span>
              <div className="w-full rounded-t bg-brand-500" style={{ height: `${(item.count / maxHour) * 100}px` }} />
              <span className="text-xs text-slate-400">{item.hour}</span>
            </div>
          ))}
        </div>
      </div>

      {data.by_method.length > 0 && (
        <div className="card mt-4">
          <h2 className="mb-3 font-medium">{t('st.methods')}</h2>
          <div className="space-y-1 text-sm">
            {data.by_method.map((item) => (
              <div key={item.method} className="flex justify-between">
                <span>{t('p.' + item.method)}</span>
                <span className="font-medium">{item.amount.toLocaleString('ru-RU')} ₸</span>
              </div>
            ))}
          </div>
        </div>
      )}

      {data.comments.length > 0 && (
        <div className="card mt-4">
          <h2 className="mb-3 font-medium">{t('st.comments')}</h2>
          <div className="space-y-3 text-sm">
            {data.comments.map((item, index) => (
              <div key={index}>
                <div className="text-amber-400">{'★'.repeat(item.rating)}</div>
                <div>“{item.comment}”</div>
                <div className="text-xs text-slate-500">{item.doctor}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="card mt-4">
        <h2 className="mb-3 font-medium">{t('st.doctors')}</h2>
        <div className="space-y-3">
          {data.by_doctor.map((item) => (
            <div key={item.doctor} className="flex items-center justify-between gap-3 text-sm">
              <div>
                <div className="font-medium">{item.doctor}</div>
                <div className="text-xs text-slate-500">
                  {t('sp.' + item.specialty, item.specialty)} · {item.completed} {t('st.completed')}
                </div>
              </div>
              <div className="text-right">
                <div>
                  ~{item.visit_minutes} {t('t.min')}
                </div>
                <div className="text-xs text-slate-500">
                  {item.real_data ? t('st.real') : t('st.default')} · {item.rating ? `${item.rating} ★` : t('st.noratings')}
                </div>
              </div>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
