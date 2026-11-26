import { useCallback, useEffect, useState } from 'react'
import { QRCodeSVG } from 'qrcode.react'
import { Link } from 'react-router-dom'
import api, { getErrorText } from '../api.js'
import { StatusBadge } from '../components/Badge.jsx'
import BackLink from '../components/BackLink.jsx'
import { useLang } from '../i18n.jsx'
import { getProfile, getTokens, saveProfile } from '../visits.js'

const ACTIVE = ['booked', 'checked_in', 'in_progress']

function readToken() {
  try {
    return localStorage.getItem('patientToken') || ''
  } catch {
    return ''
  }
}

function VisitCard({ item, rebook }) {
  const { t, locale } = useLang()
  return (
    <div className="card">
      <Link to={`/track/${item.token}`} className="flex items-center justify-between gap-3">
        <div>
          <div className="font-medium">
            {item.doctor} <span className="text-sm text-slate-500">({t('sp.' + item.specialty, item.specialty)})</span>
          </div>
          <div className="text-sm text-slate-500">
            {new Date(item.slot_start).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'short', hour12: false })}
          </div>
        </div>
        <StatusBadge status={item.status} />
      </Link>
      {item.status !== 'cancelled' && item.status !== 'no_show' && (
        <div className="mt-3 flex items-center justify-between gap-2 rounded-xl bg-slate-50 px-3 py-2 text-sm">
          {item.payment && item.payment.status === 'paid' ? (
            <span className="text-brand-700">
              ✓ {t('p.paidshort')}: {item.payment.amount === 0 ? t('p.free') : `${item.payment.amount.toLocaleString('ru-RU')} ₸`} ·{' '}
              {t('p.' + item.payment.method)}
            </span>
          ) : item.status === 'completed' && item.billed ? (
            <>
              <span className="font-medium">
                {t('p.topay')}: {item.price.toLocaleString('ru-RU')} ₸
              </span>
              <Link to={`/track/${item.token}`} className="btn px-3 py-1 text-sm">
                {t('p.payshort')}
              </Link>
            </>
          ) : (
            <span className="text-slate-600">{t('p.doctorprice')}</span>
          )}
        </div>
      )}
      {rebook && !ACTIVE.includes(item.status) && (
        <Link to={`/clinics/${item.clinic_slug}/questions`} className="btn-light mt-3 px-3 py-1 text-sm">
          {t('my.rebook')}
        </Link>
      )}
    </div>
  )
}

function saveSession(data) {
  try {
    localStorage.setItem('patientToken', data.token)
  } catch {
    return
  }
}

function Login({ onLogin }) {
  const { t } = useLang()
  const [mode, setMode] = useState('login')
  const [name, setName] = useState(getProfile().name)
  const [phone, setPhone] = useState(getProfile().phone)
  const [pin, setPin] = useState('')
  const [error, setError] = useState('')
  const [bot, setBot] = useState('')
  const [waiting, setWaiting] = useState(false)
  const [forgot, setForgot] = useState(false)
  const [tg, setTg] = useState(null)

  useEffect(() => {
    api.get('/config/').then((response) => setBot(response.data.telegram_bot || ''))
  }, [])

  function submit(event) {
    event.preventDefault()
    setError('')
    const request =
      mode === 'login'
        ? api.post('/patient/login/', { phone, pin })
        : api.post('/patient/register/', { full_name: name, phone, pin })
    request
      .then((response) => {
        saveSession(response.data)
        onLogin()
      })
      .catch((err) => {
        if (mode === 'login' && err.response && err.response.status === 400) {
          setError(t('my.wrong'))
        } else {
          setError(getErrorText(err))
        }
      })
  }

  async function telegram() {
    setError('')
    try {
      const started = await api.post('/patient/telegram/start/')
      setTg(started.data)
      window.open(started.data.link, '_blank', 'noopener')
      setWaiting(true)
      for (let attempt = 0; attempt < 150; attempt += 1) {
        await new Promise((resolve) => setTimeout(resolve, 2000))
        const result = await api.post('/patient/telegram/check/', { nonce: started.data.nonce })
        if (result.data.token) {
          saveSession(result.data)
          onLogin()
          return
        }
      }
      setError(t('my.tgfail'))
    } catch {
      setError(t('my.tgfail'))
    }
    setWaiting(false)
    setTg(null)
  }

  return (
    <div className="card mt-4">
      <div className="mb-4 grid grid-cols-2 gap-1 rounded-xl bg-slate-100 p-1 text-sm">
        {[
          ['login', t('my.haveprofile')],
          ['register', t('my.noprofile')],
        ].map(([key, label]) => (
          <button
            key={key}
            type="button"
            onClick={() => {
              setMode(key)
              setError('')
            }}
            className={`rounded-lg px-2 py-2 ${mode === key ? 'bg-white font-medium shadow-sm' : 'text-slate-600'}`}
          >
            {label}
          </button>
        ))}
      </div>

      {bot && (
        <>
          <button type="button" onClick={telegram} disabled={waiting} className="btn w-full">
            ✈ {t('my.tg')}
          </button>
          <p className="mt-2 text-xs text-slate-500">{waiting ? t('my.tgwait') : t('my.tgnote')}</p>
          {tg && (
            <div className="mt-3 rounded-xl bg-slate-50 p-3 text-sm">
              <a href={tg.link} target="_blank" rel="noreferrer" className="btn-light w-full">
                {t('my.tgopen')}
              </a>
              <div className="mt-3 flex items-center gap-3">
                <QRCodeSVG value={tg.link} size={96} />
                <p className="text-xs text-slate-500">{t('my.tgqr')}</p>
              </div>
              <p className="mt-3 text-xs text-slate-500">{t('my.tgmanual')}</p>
              <code className="mt-1 block select-all rounded-lg bg-white px-2 py-1 text-xs">/start login_{tg.nonce}</code>
            </div>
          )}
          <div className="my-3 text-center text-xs text-slate-400">{t('my.or')}</div>
        </>
      )}

      <form onSubmit={submit}>
        <div className="grid gap-3 sm:grid-cols-2">
          {mode === 'register' && (
            <input className="input sm:col-span-2" placeholder={t('my.name')} value={name} onChange={(event) => setName(event.target.value)} />
          )}
          <input className="input" placeholder={t('my.phone')} value={phone} onChange={(event) => setPhone(event.target.value)} />
          <input
            className="input"
            type="password"
            inputMode="numeric"
            maxLength={6}
            placeholder={t('pin.ph')}
            value={pin}
            onChange={(event) => setPin(event.target.value)}
          />
        </div>
        {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
        <button className="btn-light mt-3 w-full">{mode === 'login' ? t('my.enter') : t('my.create')}</button>
        {mode === 'login' && (
          <button type="button" onClick={() => setForgot(!forgot)} className="mt-2 text-sm text-slate-500 underline">
            {t('f.pin')}
          </button>
        )}
        {forgot && mode === 'login' && (
          <div className="mt-2 rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
            {bot ? (
              <>
                <p>{t('f.pinhelp_tg')}</p>
                <button type="button" onClick={telegram} disabled={waiting} className="btn mt-2">
                  ✈ {t('my.tg')}
                </button>
              </>
            ) : (
              <p>{t('f.pinhelp_clinic')}</p>
            )}
          </div>
        )}
        <p className="mt-2 text-xs text-slate-500">{mode === 'register' ? t('my.registerhint') : t('my.hint2')}</p>
        {!bot && <p className="mt-1 text-xs text-slate-400">{t('my.safety')}</p>}
      </form>
    </div>
  )
}

function Cabinet({ onLogout }) {
  const { t, locale } = useLang()
  const [data, setData] = useState(null)
  const [form, setForm] = useState({ full_name: '', birth_date: '', conditions: '' })
  const [saved, setSaved] = useState(false)
  const [newPin, setNewPin] = useState('')
  const [pinMessage, setPinMessage] = useState('')

  const header = { headers: { 'X-Patient-Token': readToken() } }

  const load = useCallback(() => {
    api
      .get('/patient/me/', { headers: { 'X-Patient-Token': readToken() } })
      .then((response) => {
        setData(response.data)
        setForm({
          full_name: response.data.profile.full_name,
          birth_date: response.data.profile.birth_date || '',
          conditions: response.data.profile.conditions || '',
        })
      })
      .catch(onLogout)
  }, [onLogout])

  useEffect(() => {
    load()
  }, [load])

  function save(event) {
    event.preventDefault()
    const body = { full_name: form.full_name, conditions: form.conditions, birth_date: form.birth_date || null }
    api.patch('/patient/me/', body, header).then((response) => {
      setData(response.data)
      setSaved(true)
    })
  }

  function change(next) {
    setForm(next)
    setSaved(false)
  }

  function changePin(event) {
    event.preventDefault()
    setPinMessage('')
    api
      .post('/patient/me/pin/', { pin: newPin }, header)
      .then(() => {
        setNewPin('')
        setPinMessage(`✓ ${t('f.pinsaved')}`)
      })
      .catch((err) => setPinMessage(getErrorText(err)))
  }

  if (!data) return <p className="mt-4 text-slate-500">{t('loading')}</p>

  const active = data.visits.filter((item) => ACTIVE.includes(item.status))
  const history = data.visits.filter((item) => !ACTIVE.includes(item.status))

  return (
    <div>
      <div className="mt-4 flex items-center justify-between">
        <div>
          <div className="text-xl font-semibold">{data.profile.full_name}</div>
          <div className="text-sm text-slate-500">{data.profile.phone}</div>
        </div>
        <button onClick={onLogout} className="text-sm text-slate-500 underline">
          {t('my.logout')}
        </button>
      </div>

      <div className="card mt-4">
        <div className="text-sm text-slate-500">{t('my.last')}</div>
        <div className="text-lg font-semibold">
          {data.last_visit ? new Date(data.last_visit).toLocaleDateString(locale, { dateStyle: 'long' }) : t('my.never')}
        </div>
      </div>

      <form onSubmit={save} className="card mt-4">
        <h2 className="mb-3 font-medium">{t('my.profile')}</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <input
            className="input"
            placeholder={t('my.name')}
            value={form.full_name}
            onChange={(event) => change({ ...form, full_name: event.target.value })}
          />
          <input
            className="input"
            type="date"
            value={form.birth_date}
            onChange={(event) => change({ ...form, birth_date: event.target.value })}
          />
        </div>
        <label className="mt-3 block text-sm font-medium">{t('my.conditions')}</label>
        <textarea
          className="input mt-1"
          rows={2}
          value={form.conditions}
          onChange={(event) => change({ ...form, conditions: event.target.value })}
        />
        <button
          disabled={saved}
          className={`mt-3 rounded-xl px-5 py-2.5 font-medium transition-colors duration-300 ${
            saved ? 'bg-brand-100 text-brand-700' : 'bg-brand-600 text-white hover:bg-brand-700'
          }`}
        >
          {saved ? `✓ ${t('v.saved')}` : t('my.save')}
        </button>
      </form>

      <form onSubmit={changePin} className="card mt-4">
        <h2 className="mb-3 font-medium">{t('f.changepin')}</h2>
        <div className="flex gap-2">
          <input
            className="input"
            type="password"
            inputMode="numeric"
            maxLength={6}
            placeholder={t('f.newpin')}
            value={newPin}
            onChange={(event) => setNewPin(event.target.value)}
          />
          <button disabled={newPin.length < 4} className="btn shrink-0">
            {t('my.save')}
          </button>
        </div>
        {pinMessage && <p className="mt-2 text-sm text-brand-700">{pinMessage}</p>}
      </form>

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

      <h2 className="mb-2 mt-6 font-medium">{t('my.records')}</h2>
      {data.records.length === 0 && <p className="text-sm text-slate-500">{t('my.norecords')}</p>}
      <div className="space-y-3">
        {data.records.map((record) => (
          <div key={record.id} className="card text-sm">
            <div className="flex items-center justify-between gap-2">
              <span className="font-medium">{record.title}</span>
              <span className="rounded-full bg-brand-100 px-2 py-0.5 text-xs text-brand-700">{t('rk.' + record.kind)}</span>
            </div>
            {record.text && <p className="mt-1 whitespace-pre-line text-slate-600">{record.text}</p>}
            <p className="mt-1 text-xs text-slate-400">
              {new Date(record.created_at).toLocaleDateString(locale, { dateStyle: 'medium' })} · {record.author}
            </p>
          </div>
        ))}
      </div>

      {history.length > 0 && (
        <>
          <h2 className="mb-2 mt-6 font-medium">{t('v.history')}</h2>
          <div className="space-y-3">
            {history.map((item) => (
              <VisitCard key={item.token} item={item} rebook />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

function LocalVisits() {
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
  }

  function change(next) {
    setProfile(next)
    setSaved(false)
  }

  const active = visits.filter((item) => ACTIVE.includes(item.status))
  const history = visits.filter((item) => !ACTIVE.includes(item.status))

  return (
    <div>
      <form onSubmit={save} className="card mt-4">
        <h2 className="mb-3 font-medium">{t('v.profile')}</h2>
        <div className="grid gap-3 sm:grid-cols-2">
          <input
            className="input"
            placeholder={t('b.name')}
            value={profile.name}
            onChange={(event) => change({ ...profile, name: event.target.value })}
          />
          <input
            className="input"
            placeholder="+7 701 123 45 67"
            value={profile.phone}
            onChange={(event) => change({ ...profile, phone: event.target.value })}
          />
        </div>
        <div className="mt-3 flex items-center gap-3">
          <button
            disabled={saved}
            className={`rounded-xl px-5 py-2.5 font-medium transition-colors duration-300 ${
              saved ? 'bg-brand-100 text-brand-700' : 'bg-brand-600 text-white hover:bg-brand-700'
            }`}
          >
            {saved ? `✓ ${t('v.saved')}` : t('v.save')}
          </button>
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
              <VisitCard key={item.token} item={item} rebook />
            ))}
          </div>
        </>
      )}
    </div>
  )
}

export default function MyVisits() {
  const { t } = useLang()
  const [loggedIn, setLoggedIn] = useState(Boolean(readToken()))

  const logout = useCallback(() => {
    try {
      localStorage.removeItem('patientToken')
    } catch {
      setLoggedIn(false)
    }
    setLoggedIn(false)
  }, [])

  return (
    <div>
      <BackLink to="/" />
      <h1 className="text-2xl font-semibold">{t('v.title')}</h1>
      {loggedIn ? (
        <Cabinet onLogout={logout} />
      ) : (
        <>
          <Login onLogin={() => setLoggedIn(true)} />
          <LocalVisits />
        </>
      )}
    </div>
  )
}
