import { Link } from 'react-router-dom'

export default function EmptyState({ title, text, to, action }) {
  return (
    <div className="card mx-auto mt-8 max-w-md text-center">
      <h1 className="text-xl font-semibold">{title}</h1>
      <p className="mt-2 text-slate-600">{text}</p>
      {to && (
        <Link to={to} className="btn mt-5">
          {action}
        </Link>
      )}
    </div>
  )
}
