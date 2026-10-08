import { Link } from 'react-router-dom'

export default function Header() {
  return (
    <header className="border-b border-slate-200 bg-white">
      <div className="mx-auto flex max-w-2xl items-center justify-between px-4 py-3">
        <Link to="/" className="text-lg font-semibold text-brand-700">
          KezekKz
        </Link>
        <span className="text-xs text-slate-500">Smart patient queue</span>
      </div>
    </header>
  )
}
