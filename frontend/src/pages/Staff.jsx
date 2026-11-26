import { useCallback, useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { getErrorText } from '../api.js'
import { StatusBadge } from '../components/Badge.jsx'
import { useLang } from '../i18n.jsx'

const URGENCY = ['routine', 'priority', 'urgent']

const STATUS_BUTTONS = ['checked_in', 'in_progress', 'completed', 'no_show']

function authHeader() {
  return { headers: { Authorization: `Token ${localStorage.getItem('staffToken')}` } }
}

function BillForm({ item, onSet }) {
  const { t } = useLang()
  const [price, setPrice] = useState(String(item.price))
  const valid = price !== '' && Number(price) >= 0
  return (
    <div className="flex flex-wrap items-center gap-2">
      <span className="text-slate-600">{t('s.billprice')}:</span>
      <input
        type="number"
        min="0"
        step="500"
        value={price}
        onChange={(event) => setPrice(event.target.value)}
        className="input w-32 py-1"
      />
      <button disabled={!valid} onClick={() => onSet(item.id, Number(price))} className="btn px-3 py-1 text-sm">
        {t('s.billnow')}
      </button>
    </div>
  )
}


function Login({ onLogin }) {
  const { t } = useLang()
  const [help, setHelp] = useState(false)
  const adminUrl = new URL(import.meta.env.VITE_API_URL || 'http://localhost:8000/api').origin + '/admin/'
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  function submit(event) {
    event.preventDefault()
    api
      .post('/auth/token/', { username, password })
      .then((response) => {
        localStorage.setItem('staffToken', response.data.token)
        window.dispatchEvent(new Event('staff-auth'))
        onLogin()
      })
      .catch((err) => {
        if (err.response && err.response.status === 400) {
          setError(t('s.wrong'))
        } else {
          setError(getErrorText(err))
        }
      })
  }

  return (
    <form onSubmit={submit} className="card mx-auto max-w-sm space-y-3">
      <h1 className="text-xl font-semibold">{t('s.login')}</h1>
      <input
        className="input"
        placeholder={t('s.user')}
        value={username}
        onChange={(event) => setUsername(event.target.value)}
      />
      <input
        className="input"
        type="password"
        placeholder={t('s.pass')}
        value={password}
        onChange={(event) => setPassword(event.target.value)}
      />
      {error && <p className="text-red-600">{error}</p>}
      <button className="btn w-full">{t('s.in')}</button>
      <button type="button" onClick={() => setHelp(!help)} className="w-full text-center text-sm text-slate-500 underline">
        {t('f.staff')}
      </button>
      {help && (
        <div className="rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
          <p>{t('f.staffhelp')}</p>
          <a href={adminUrl} target="_blank" rel="noreferrer" className="mt-2 inline-block text-brand-600 underline">
            {t('f.admin')}
          </a>
        </div>
      )}
    </form>
  )
}

function Dashboard({ onLogout }) {
  const { t, reasonText } = useLang()
  const [doctors, setDoctors] = useState([])
  const [doctorId, setDoctorId] = useState('')
  const [queue, setQueue] = useState([])
  const [delay, setDelay] = useState(0)
  const [pending, setPending] = useState([])
  const [date, setDate] = useState(() => new Date().toLocaleDateString('sv-SE'))
  const [error, setError] = useState('')

  useEffect(() => {
    api.get('/clinics/').then((response) => {
      api.get(`/clinics/${response.data[0].slug}/doctors/`).then((result) => {
        setDoctors(result.data)
        if (result.data.length > 0) {
          setDoctorId(String(result.data[0].id))
          setDelay(result.data[0].delay_minutes)
        }
      })
    })
  }, [])

  const load = useCallback(() => {
    if (!doctorId) return
    api
      .get(`/staff/queue/?doctor=${doctorId}&date=${date}`, authHeader())
      .then((response) => {
        setQueue(response.data)
        setError('')
      })
      .catch((err) => {
        if (err.response && err.response.status === 401) {
          onLogout()
        } else {
          setError(getErrorText(err))
        }
      })
  }, [doctorId, date, onLogout])

  const loadPending = useCallback(() => {
    api
      .get('/staff/payments/pending/', authHeader())
      .then((response) => setPending(response.data))
      .catch(() => setPending([]))
  }, [])

  useEffect(() => {
    load()
    loadPending()
    const timer = setInterval(() => {
      load()
      loadPending()
    }, 10000)
    return () => clearInterval(timer)
  }, [load, loadPending])

  function update(id, data) {
    api
      .patch(`/staff/appointments/${id}/`, data, authHeader())
      .then(load)
      .catch((err) => setError(getErrorText(err)))
  }

  function setPrice(id, price) {
    update(id, { status: 'completed', final_price: price })
  }

  function markPaid(id) {
    api
      .post(`/staff/appointments/${id}/mark-paid/`, {}, authHeader())
      .then(loadPending)
      .catch((err) => setError(getErrorText(err)))
  }

  function changeDoctor(id) {
    setDoctorId(id)
    const doctor = doctors.find((item) => String(item.id) === id)
    setDelay(doctor ? doctor.delay_minutes : 0)
  }

  function saveDelay() {
    api
      .patch(`/staff/doctors/${doctorId}/`, { delay_minutes: Number(delay) }, authHeader())
      .then(() => {
        setDoctors(doctors.map((item) => (String(item.id) === doctorId ? { ...item, delay_minutes: Number(delay) } : item)))
        load()
      })
      .catch((err) => setError(getErrorText(err)))
  }

  const urgentCount = queue.filter((item) => item.urgency === 'urgent').length
  const waits = queue.filter((item) => item.queue.wait_minutes !== null).map((item) => item.queue.wait_minutes)
  const averageWait = waits.length ? Math.round(waits.reduce((a, b) => a + b, 0) / waits.length) : 0

  return (
    <div>
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{t('s.title')}</h1>
      </div>

      <div className="mt-4 grid grid-cols-3 gap-3">
        {[
          [t('s.waiting'), queue.length],
          [t('s.urgent'), urgentCount],
          [t('s.avg'), `${averageWait} ${t('t.min')}`],
        ].map(([label, value]) => (
          <div key={label} className="card text-center">
            <div className="text-2xl font-bold text-brand-700">{value}</div>
            <div className="text-xs text-slate-500">{label}</div>
          </div>
        ))}
      </div>

      <div className="mt-3 flex flex-wrap items-end gap-3">
        <select
          className="input w-auto"
          value={doctorId}
          onChange={(event) => changeDoctor(event.target.value)}
        >
          {doctors.map((doctor) => (
            <option key={doctor.id} value={doctor.id}>
              {doctor.full_name} ({t('sp.' + doctor.specialty, doctor.specialty)})
            </option>
          ))}
        </select>
        <input type="date" className="input w-auto" value={date} onChange={(event) => setDate(event.target.value)} />
        <label className="text-sm text-slate-600">
          {t('s.late')}
          <input
            type="number"
            min="0"
            max="240"
            className="input ml-2 w-20 py-1"
            value={delay}
            onChange={(event) => setDelay(event.target.value)}
          />
        </label>
        <button onClick={saveDelay} className="btn-light">
          {t('s.save')}
        </button>
      </div>

      {pending.length > 0 && (
        <div className="card mt-4 border-amber-200 bg-amber-50">
          <h2 className="font-medium">{t('s.pending')}</h2>
          <div className="mt-2 space-y-2">
            {pending.map((item) => (
              <div key={item.id} className="flex items-center justify-between gap-2 text-sm">
                <span>
                  {item.patient_name} · {item.payment.amount.toLocaleString('ru-RU')} ₸
                </span>
                <button onClick={() => markPaid(item.id)} className="btn px-3 py-1 text-sm">
                  {t('s.takepay')}
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {error && <p className="mt-3 text-red-600">{error}</p>}
      {queue.length === 0 && <p className="mt-4 text-slate-500">{t('s.empty')}</p>}

      <div className="mt-4 space-y-3">
        {queue.map((item) => (
          <div key={item.id} className="card">
            <div className="flex items-start justify-between gap-2">
              <div>
                <div className="font-medium">
                  #{item.queue_number} {item.patient_name}
                </div>
                <div className="text-sm text-slate-500">
                  {item.patient_phone} · {new Date(item.slot_start).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit', hour12: false })}
                </div>
                <div className="mt-1 text-sm text-slate-600">{item.reasons.map(reasonText).join(', ')}</div>
                <div className="mt-1 space-y-0.5 text-sm text-slate-600">
                  {item.intake_summary.reason_text && (
                    <p>
                      {t('s.reasonlabel')}: {item.intake_summary.reason_text}
                    </p>
                  )}
                  {item.intake_summary.symptoms && (
                    <p>
                      {t('s.symptoms')}: {item.intake_summary.symptoms.map((code) => t('sym.' + code, code)).join(', ')}
                      {item.intake_summary.symptoms_text ? `; ${item.intake_summary.symptoms_text}` : ''}
                    </p>
                  )}
                  {!item.intake_summary.symptoms && item.intake_summary.symptoms_text && (
                    <p>
                      {t('s.symptoms')}: {item.intake_summary.symptoms_text}
                    </p>
                  )}
                  {item.intake_summary.conditions_text && (
                    <p className="text-amber-700">
                      ⚠ {t('s.condition')}: {item.intake_summary.conditions_text}
                    </p>
                  )}
                </div>
                <div className="mt-1 text-xs">
                  {t('s.risk')}:{' '}
                  <span
                    className={`rounded-full px-2 py-0.5 font-medium ${
                      { low: 'bg-emerald-100 text-emerald-800', medium: 'bg-amber-100 text-amber-800', high: 'bg-red-100 text-red-700' }[item.no_show_risk]
                    }`}
                  >
                    {t('risk.' + item.no_show_risk)}
                  </span>
                  {item.patient_confirmed && <span className="ml-2 text-brand-700">✓ {t('s.patientok')}</span>}
                </div>
              </div>
              <div className="text-right text-sm">
                <StatusBadge status={item.status} />
                {item.queue.position && (
                  <div className="text-slate-500">
                    {t('t.position')} {item.queue.position} · ~{item.queue.wait_minutes} {t('t.min')}
                  </div>
                )}
              </div>
            </div>

            <div className="mt-3 flex flex-wrap items-center gap-2">
              <select
                className="input w-auto py-1 text-sm"
                value={item.urgency}
                onChange={(event) => update(item.id, { urgency: event.target.value })}
              >
                {URGENCY.map((level) => (
                  <option key={level} value={level}>
                    {t('urgency.' + level)}
                  </option>
                ))}
              </select>
              {item.urgency_confirmed ? (
                <span className="text-sm text-brand-700">✓ {t('s.confirmed')}</span>
              ) : (
                <button
                  onClick={() => update(item.id, { urgency: item.urgency })}
                  className="btn px-3 py-1 text-sm"
                >
                  {t('s.confirmurg')}
                </button>
              )}
              {STATUS_BUTTONS.map((status) => (
                <button key={status} onClick={() => update(item.id, { status })} className="btn-light px-3 py-1 text-sm">
                  {t('act.' + status)}
                </button>
              ))}
              <Link to={`/staff/patients/${item.patient_id}`} className="btn-light px-3 py-1 text-sm">
                📋 {t('s.card')}
              </Link>
            </div>

            {['checked_in', 'in_progress'].includes(item.status) && (
              <div className="mt-3 rounded-xl bg-slate-50 p-3 text-sm text-slate-600">{t('s.setprice')}</div>
            )}

            {item.status === 'completed' && (
              <div className="mt-3 rounded-xl bg-slate-50 p-3 text-sm">
                {!item.billed && <BillForm item={item} onSet={setPrice} />}
                {item.billed && !item.payment && (
                  <p className="text-slate-600">
                    {t('s.billed')}: {item.price.toLocaleString('ru-RU')} ₸ · {t('s.waitpay')}
                  </p>
                )}
                {item.payment && item.payment.status === 'paid' && (
                  <p className="text-brand-700">
                    ✓ {t('s.paidby')}: {t('p.' + item.payment.method)} · {item.payment.amount.toLocaleString('ru-RU')} ₸ ·{' '}
                    {t('p.receipt')} № {item.payment.receipt_number}
                  </p>
                )}
                {item.payment && item.payment.status !== 'paid' && (
                  <div className="flex items-center justify-between gap-2">
                    <span className="text-amber-700">
                      {t('p.pending')} · {item.payment.amount.toLocaleString('ru-RU')} ₸
                    </span>
                    <button onClick={() => markPaid(item.id)} className="btn px-3 py-1 text-sm">
                      {t('s.takepay')}
                    </button>
                  </div>
                )}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}

export default function Staff() {
  const [loggedIn, setLoggedIn] = useState(Boolean(localStorage.getItem('staffToken')))

  const logout = useCallback(() => {
    localStorage.removeItem('staffToken')
    window.dispatchEvent(new Event('staff-auth'))
    setLoggedIn(false)
  }, [])

  if (!loggedIn) {
    return (
      <Login onLogin={() => setLoggedIn(true)} />
    )
  }
  return <Dashboard onLogout={logout} />
}
