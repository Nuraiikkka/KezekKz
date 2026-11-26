import { useState } from 'react'
import { Link } from 'react-router-dom'
import api, { getErrorText } from '../api.js'
import { useLang } from '../i18n.jsx'

export default function PinCard({ appointment, token }) {
  const { t } = useLang()
  const [pin, setPin] = useState('')
  const [error, setError] = useState('')
  const [done, setDone] = useState(false)

  let loggedIn = false
  try {
    loggedIn = Boolean(localStorage.getItem('patientToken'))
  } catch {
    loggedIn = false
  }

  function create() {
    setError('')
    api
      .post('/patient/pin/', { token, pin })
      .then((response) => {
        try {
          localStorage.setItem('patientToken', response.data.token)
        } catch {
          setError('')
        }
        setDone(true)
      })
      .catch((err) => setError(getErrorText(err)))
  }

  if (done || loggedIn || appointment.has_profile) {
    return (
      <div className="card mt-4 flex items-center justify-between gap-3 text-sm">
        <span className="text-brand-700">✓ {done ? t('pin.done') : t('pin.open')}</span>
        <Link to="/my" className="btn-light shrink-0">
          {t('pin.open')}
        </Link>
      </div>
    )
  }

  return (
    <div className="card mt-4">
      <h2 className="font-medium">{t('pin.title')}</h2>
      <p className="mt-1 text-sm text-slate-600">{t('pin.text')}</p>
      <div className="mt-3 flex gap-2">
        <input
          className="input"
          type="password"
          inputMode="numeric"
          maxLength={6}
          placeholder={t('pin.ph')}
          value={pin}
          onChange={(event) => setPin(event.target.value)}
        />
        <button onClick={create} disabled={pin.length < 4} className="btn shrink-0">
          {t('pin.create')}
        </button>
      </div>
      {error && <p className="mt-2 text-sm text-red-600">{error}</p>}
    </div>
  )
}
