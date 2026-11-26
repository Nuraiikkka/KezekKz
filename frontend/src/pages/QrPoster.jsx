import { QRCodeSVG } from 'qrcode.react'
import BackLink from '../components/BackLink.jsx'
import { useLang } from '../i18n.jsx'

export default function QrPoster() {
  const { t } = useLang()

  return (
    <div className="mx-auto max-w-md text-center">
      <div className="text-left">
        <BackLink to="/staff" />
      </div>
      <div className="card py-8">
        <div className="mx-auto mb-3 flex h-12 w-12 items-center justify-center rounded-xl bg-brand-600 text-2xl text-white">K</div>
        <h1 className="text-3xl font-bold text-brand-700">{t('qr.title')}</h1>
        <div className="mx-auto mt-6 inline-block rounded-2xl border-4 border-brand-600 bg-white p-4">
          <QRCodeSVG value={window.location.origin} size={220} />
        </div>
        <p className="mt-4 text-slate-600">{t('qr.text')}</p>
        <p className="mt-1 text-xs text-slate-400">{window.location.origin}</p>
      </div>
      <button onClick={() => window.print()} className="btn mt-4 print:hidden">
        {t('qr.print')}
      </button>
    </div>
  )
}
