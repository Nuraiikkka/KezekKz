import { QRCodeSVG } from 'qrcode.react'
import { useState } from 'react'
import api, { getErrorText } from '../api.js'
import { useLang } from '../i18n.jsx'

const METHODS = ['kaspi', 'card', 'insurance', 'cash']

function formatMoney(value) {
  return `${value.toLocaleString('ru-RU')} ₸`
}

function Receipt({ appointment }) {
  const { t, locale } = useLang()
  const payment = appointment.payment
  const paid = payment.status === 'paid'

  return (
    <div className="card mt-4">
      <div className="flex items-center justify-between">
        <h2 className="font-medium">{t('p.receipt')}</h2>
        <span
          className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${paid ? 'bg-emerald-100 text-emerald-800' : 'bg-amber-100 text-amber-800'}`}
        >
          {paid ? t('p.paid') : t('p.pending')}
        </span>
      </div>
      <div className="mt-3 space-y-1 text-sm">
        <p>
          <span className="text-slate-500">№</span> {payment.receipt_number}
        </p>
        <p>
          <span className="text-slate-500">{t('t.doctor')}:</span> {appointment.doctor}
        </p>
        <p>
          <span className="text-slate-500">{t('p.method')}:</span> {t('p.' + payment.method)}
          {payment.card_last4 && ` ${t('p.card4')}${payment.card_last4}`}
        </p>
        {payment.paid_at && (
          <p>
            <span className="text-slate-500">{t('t.time')}:</span>{' '}
            {new Date(payment.paid_at).toLocaleString(locale, { dateStyle: 'medium', timeStyle: 'short', hour12: false })}
          </p>
        )}
        <p className="pt-1 text-lg font-semibold">{payment.amount === 0 ? t('p.free') : formatMoney(payment.amount)}</p>
      </div>
      <button onClick={() => window.print()} className="btn-light mt-3">
        {t('p.print')}
      </button>
    </div>
  )
}

export default function Pay({ appointment, onChange }) {
  const { t } = useLang()
  const [method, setMethod] = useState('kaspi')
  const [cardNumber, setCardNumber] = useState('')
  const [expiry, setExpiry] = useState('')
  const [cvc, setCvc] = useState('')
  const [iin, setIin] = useState('')
  const [error, setError] = useState('')

  if (appointment.payment) {
    return <Receipt appointment={appointment} />
  }

  function pay() {
    setError('')
    const data = { method }
    if (method === 'card') data.card_number = cardNumber
    if (method === 'insurance') data.iin = iin
    api
      .post(`/appointments/${appointment.token}/pay/`, data)
      .then((response) => onChange(response.data))
      .catch((err) => setError(getErrorText(err)))
  }

  return (
    <div className="card mt-4">
      <h2 className="font-medium">{t('p.title')}</h2>
      <div className="mt-1 text-2xl font-bold text-brand-700">{formatMoney(appointment.price)}</div>
      <p className="text-xs text-slate-500">{t('p.demo')}</p>

      <div className="mt-3 grid grid-cols-2 gap-2 sm:grid-cols-4">
        {METHODS.map((item) => (
          <button
            key={item}
            onClick={() => setMethod(item)}
            className={`rounded-xl border px-2 py-2 text-sm transition ${
              method === item ? 'border-brand-600 bg-brand-50 font-medium text-brand-700' : 'border-slate-200 hover:bg-slate-50'
            }`}
          >
            {t('p.' + item)}
          </button>
        ))}
      </div>

      <div className="mt-4">
        {method === 'kaspi' && (
          <div className="flex flex-col items-center gap-2">
            <div className="rounded-xl border border-slate-200 bg-white p-3">
              <QRCodeSVG value={`kezekkz-demo-pay:${appointment.token}`} size={140} />
            </div>
            <p className="text-sm text-slate-500">{t('p.kaspihint')}</p>
          </div>
        )}

        {method === 'card' && (
          <div className="space-y-2">
            <input
              className="input"
              inputMode="numeric"
              placeholder={t('p.cardnumber')}
              value={cardNumber}
              onChange={(event) => setCardNumber(event.target.value)}
            />
            <div className="grid grid-cols-2 gap-2">
              <input className="input" placeholder={t('p.expiry')} value={expiry} onChange={(event) => setExpiry(event.target.value)} />
              <input className="input" placeholder={t('p.cvc')} value={cvc} onChange={(event) => setCvc(event.target.value)} />
            </div>
            <p className="text-xs text-slate-500">4242 4242 4242 4242</p>
          </div>
        )}

        {method === 'insurance' && (
          <div className="space-y-2">
            <p className="text-sm text-slate-600">{t('p.insurancehint')}</p>
            <input className="input" inputMode="numeric" placeholder={t('p.iin')} value={iin} onChange={(event) => setIin(event.target.value)} />
          </div>
        )}

        {method === 'cash' && <p className="text-sm text-slate-600">{t('p.cashhint')}</p>}
      </div>

      {error && <p className="mt-3 text-red-600">{error}</p>}

      <button onClick={pay} className="btn mt-4 w-full">
        {method === 'kaspi' ? t('p.kaspidone') : t('p.pay')}
      </button>
    </div>
  )
}
