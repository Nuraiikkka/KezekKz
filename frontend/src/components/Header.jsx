import { Link, NavLink } from 'react-router-dom'
import { useLang } from '../i18n.jsx'

const LANGS = ['ru', 'kk', 'en']

export default function Header() {
  const { lang, setLang, t } = useLang()

  function linkClass({ isActive }) {
    return `whitespace-nowrap rounded-lg px-2.5 py-1.5 text-sm ${isActive ? 'bg-brand-100 font-medium text-brand-700' : 'text-slate-600 hover:bg-slate-100'}`
  }

  return (
    <header className="sticky top-0 z-10 print:hidden border-b border-slate-100 bg-white/90 backdrop-blur">
      <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-2 px-4 py-3">
        <Link to="/" className="flex items-center gap-2 text-lg font-semibold text-brand-700">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-brand-600 text-white">K</span>
          KezekKz
        </Link>
        <nav className="flex flex-wrap items-center gap-1">
          <NavLink to="/" end className={linkClass}>
            {t('nav.home')}
          </NavLink>
          <NavLink to="/my" className={linkClass}>
            {t('nav.visits')}
          </NavLink>
          <NavLink to="/staff" className={linkClass}>
            {t('nav.staff')}
          </NavLink>
          <div className="ml-2 flex overflow-hidden rounded-lg border border-slate-200 text-xs">
            {LANGS.map((code) => (
              <button
                key={code}
                onClick={() => setLang(code)}
                className={`px-2 py-1 uppercase ${lang === code ? 'bg-brand-600 text-white' : 'text-slate-600'}`}
              >
                {code}
              </button>
            ))}
          </div>
        </nav>
      </div>
    </header>
  )
}
