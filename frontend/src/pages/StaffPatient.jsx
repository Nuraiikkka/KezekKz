import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import api, { getErrorText } from '../api.js'
import { StatusBadge } from '../components/Badge.jsx'
import BackLink from '../components/BackLink.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { useLang } from '../i18n.jsx'

const KINDS = ['note', 'analysis', 'prescription']

export default function StaffPatient() {
  const { id } = useParams()
  const { t, locale } = useLang()
  const [data, setData] = useState(null)
  const [denied, setDenied] = useState(false)
  const [error, setError] = useState('')
  const [message, setMessage] = useState('')
  const [form, setForm] = useState({ kind: 'note', title: '', text: '' })

  const auth = useCallback(() => ({ headers: { Authorization: `Token ${localStorage.getItem('staffToken')}` } }), [])

  useEffect(() => {
    api
      .get(`/staff/patients/${id}/`, auth())
      .then((response) => setData(response.data))
      .catch(() => setDenied(true))
  }, [id, auth])

  function add(event) {
    event.preventDefault()
    setError('')
    api
      .post(`/staff/patients/${id}/records/`, form, auth())
      .then((response) => {
        setData(response.data)
        setForm({ kind: 'note', title: '', text: '' })
      })
      .catch((err) => setError(getErrorText(err)))
  }

  function resetPin() {
    if (!window.confirm(t('f.resetconfirm'))) return
    api
      .post(`/staff/patients/${id}/reset-pin/`, {}, auth())
      .then((response) => {
        setData(response.data)
        setMessage(t('f.resetdone'))
      })
      .catch((err) => setError(getErrorText(err)))
  }

  if (denied) {
    return <EmptyState title={t('nf.staff')} text={t('nf.stafftext')} to="/staff" action={t('nf.stafflogin')} />
  }
  if (!data) return <p className="text-slate-500">{t('loading')}</p>

  const profile = data.profile
  const format = (value) => new Date(value).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'short', hour12: false })

  return (
    <div>
      <BackLink to="/staff" />
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{t('sc.title')}</h1>
        <Link to="/staff" className="text-sm text-slate-500 underline">
          {t('sc.back')}
        </Link>
      </div>

      <div className="card mt-4">
        <div className="text-xl font-semibold">{profile.full_name}</div>
        <div className="text-sm text-slate-500">
          {profile.phone}
          {profile.birth_date ? ` · ${profile.birth_date}` : ''}
        </div>
        <div className="mt-2 text-sm">
          <span className="text-slate-500">{t('sc.last')}:</span>{' '}
          {data.last_visit ? new Date(data.last_visit).toLocaleDateString(locale, { dateStyle: 'long' }) : t('my.never')}
        </div>
        <button onClick={resetPin} className="btn-light mt-3 px-3 py-1 text-sm">
          {t('f.reset')}
        </button>
        {message && <p className="mt-2 text-sm text-brand-700">{message}</p>}
        {profile.conditions && (
          <p className="mt-2 rounded-lg bg-amber-50 p-2 text-sm text-amber-800">
            {t('s.condition')}: {profile.conditions}
          </p>
        )}
      </div>

      <h2 className="mb-2 mt-6 font-medium">{t('sc.records')}</h2>
      <form onSubmit={add} className="card">
        <div className="grid gap-2 sm:grid-cols-3">
          <select className="input" value={form.kind} onChange={(event) => setForm({ ...form, kind: event.target.value })}>
            {KINDS.map((kind) => (
              <option key={kind} value={kind}>
                {t('rk.' + kind)}
              </option>
            ))}
          </select>
          <input
            className="input sm:col-span-2"
            placeholder={t('sc.titlePh')}
            value={form.title}
            onChange={(event) => setForm({ ...form, title: event.target.value })}
          />
        </div>
        <textarea
          className="input mt-2"
          rows={3}
          placeholder={t('sc.textPh')}
          value={form.text}
          onChange={(event) => setForm({ ...form, text: event.target.value })}
        />
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <button disabled={!form.title.trim()} className="btn mt-2">
          {t('sc.save')}
        </button>
      </form>

      {data.records.length === 0 && <p className="mt-3 text-sm text-slate-500">{t('sc.empty')}</p>}
      <div className="mt-3 space-y-3">
        {data.records.map((record) => (
          <div key={record.id} className="card text-sm">
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium">{record.title}</span>
              <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs text-brand-700">{t('rk.' + record.kind)}</span>
            </div>
            {record.text && <p className="mt-1 whitespace-pre-line text-slate-600">{record.text}</p>}
            <p className="mt-1 text-xs text-slate-400">
              {format(record.created_at)} · {t('sc.author')}: {record.author}
            </p>
          </div>
        ))}
      </div>

      <h2 className="mb-2 mt-6 font-medium">{t('sc.visits')}</h2>
      <div className="space-y-3">
        {data.visits.map((visit) => (
          <div key={visit.token} className="card text-sm">
            <div className="flex items-center justify-between gap-2">
              <div>
                <div className="font-medium">
                  {visit.doctor} ({t('sp.' + visit.specialty, visit.specialty)})
                </div>
                <div className="text-slate-500">{format(visit.slot_start)}</div>
              </div>
              <StatusBadge status={visit.status} />
            </div>
            {visit.intake_summary.reason_text && (
              <p className="mt-1 text-slate-600">
                {t('s.reasonlabel')}: {visit.intake_summary.reason_text}
              </p>
            )}
            {visit.intake_summary.symptoms && (
              <p className="mt-1 text-slate-600">
                {t('s.symptoms')}: {visit.intake_summary.symptoms.map((code) => t('sym.' + code, code)).join(', ')}
                {visit.intake_summary.symptoms_text ? `; ${visit.intake_summary.symptoms_text}` : ''}
              </p>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
