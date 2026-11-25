import { useLang } from '../i18n.jsx'

const URGENCY_STYLE = {
  routine: 'bg-emerald-100 text-emerald-800',
  priority: 'bg-amber-100 text-amber-800',
  urgent: 'bg-red-100 text-red-700',
}

const STATUS_STYLE = {
  booked: 'bg-sky-100 text-sky-800',
  checked_in: 'bg-indigo-100 text-indigo-800',
  in_progress: 'bg-violet-100 text-violet-800',
  completed: 'bg-emerald-100 text-emerald-800',
  no_show: 'bg-slate-200 text-slate-700',
  cancelled: 'bg-slate-200 text-slate-700',
}

export function UrgencyBadge({ urgency }) {
  const { t } = useLang()
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${URGENCY_STYLE[urgency]}`}>
      {t('urgency.' + urgency)}
    </span>
  )
}

export function StatusBadge({ status }) {
  const { t } = useLang()
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-medium ${STATUS_STYLE[status]}`}>
      {t('status.' + status)}
    </span>
  )
}
