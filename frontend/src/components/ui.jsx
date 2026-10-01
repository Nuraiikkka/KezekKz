export function Card({ children, className = '' }) {
  return <div className={`rounded-2xl bg-white p-5 shadow-sm ring-1 ring-slate-200 ${className}`}>{children}</div>
}

export function Button({ children, variant = 'primary', className = '', ...props }) {
  const styles = {
    primary: 'bg-brand-600 text-white hover:bg-brand-700 disabled:bg-slate-300',
    secondary: 'bg-white text-slate-700 ring-1 ring-slate-300 hover:bg-slate-50 disabled:text-slate-400',
    danger: 'bg-white text-red-600 ring-1 ring-red-200 hover:bg-red-50',
  }
  return (
    <button
      className={`rounded-xl px-4 py-2.5 text-sm font-medium transition disabled:cursor-not-allowed ${styles[variant]} ${className}`}
      {...props}
    >
      {children}
    </button>
  )
}

export function Spinner({ label = 'Loading…' }) {
  return (
    <div className="flex items-center gap-2 text-sm text-slate-500" role="status">
      <span className="h-4 w-4 animate-spin rounded-full border-2 border-slate-300 border-t-brand-600" />
      {label}
    </div>
  )
}

export function ErrorBox({ message, onRetry }) {
  if (!message) return null
  return (
    <div className="rounded-xl bg-red-50 p-3 text-sm text-red-700 ring-1 ring-red-200" role="alert">
      {message}
      {onRetry && (
        <button onClick={onRetry} className="ml-2 underline">
          Try again
        </button>
      )}
    </div>
  )
}

const URGENCY_STYLES = {
  urgent: 'bg-red-100 text-red-700',
  priority: 'bg-amber-100 text-amber-800',
  routine: 'bg-emerald-100 text-emerald-800',
}

export function UrgencyBadge({ urgency }) {
  return (
    <span className={`rounded-full px-2.5 py-0.5 text-xs font-semibold capitalize ${URGENCY_STYLES[urgency] || ''}`}>
      {urgency}
    </span>
  )
}
