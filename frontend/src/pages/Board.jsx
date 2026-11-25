import { useEffect, useState } from 'react'
import api from '../api.js'
import { useLang } from '../i18n.jsx'

export default function Board() {
  const { t } = useLang()
  const [rows, setRows] = useState([])
  const [clinic, setClinic] = useState(null)

  useEffect(() => {
    api.get('/clinics/').then((response) => setClinic(response.data[0]))
  }, [])

  useEffect(() => {
    if (!clinic) return
    function load() {
      api.get(`/clinics/${clinic.slug}/board/`).then((response) => setRows(response.data))
    }
    load()
    const timer = setInterval(load, 5000)
    return () => clearInterval(timer)
  }, [clinic])

  return (
    <div>
      <div className="mb-4 flex items-end justify-between">
        <h1 className="text-2xl font-semibold">{t('board.title')}</h1>
        <span className="text-sm text-slate-500">{clinic ? clinic.name : ''}</span>
      </div>

      <div className="grid gap-3 sm:grid-cols-2">
        {rows.map((row) => (
          <div key={row.doctor} className="overflow-hidden rounded-2xl bg-brand-900 text-white shadow-lg">
            <div className="flex items-center justify-between bg-brand-700 px-4 py-2 text-sm">
              <span className="truncate">{row.doctor}</span>
              <span className="rounded-md bg-white/20 px-2 py-0.5">
                {t('t.room')} {row.room}
              </span>
            </div>
            <div className="px-4 py-4 text-center">
              <div className="text-xs uppercase tracking-wide text-brand-200">{t('board.serving')}</div>
              <div className="text-7xl font-bold tabular-nums">{row.now_serving || '—'}</div>
              <div className="mt-3 text-xs uppercase tracking-wide text-brand-200">{t('board.next')}</div>
              <div className="mt-1 flex justify-center gap-2">
                {row.next.length === 0 && <span className="text-brand-200">{t('board.nobody')}</span>}
                {row.next.map((number) => (
                  <span key={number} className="rounded-lg bg-white/15 px-3 py-1 text-xl font-semibold tabular-nums">
                    {number}
                  </span>
                ))}
              </div>
              {row.delay_minutes > 0 && (
                <div className="mt-3 text-sm text-amber-300">
                  {t('board.late')}: {row.delay_minutes} {t('t.min')}
                </div>
              )}
            </div>
          </div>
        ))}
      </div>
      <p className="mt-4 text-center text-xs text-slate-500">{t('board.hint')}</p>
    </div>
  )
}
