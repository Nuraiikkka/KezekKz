import { Link, NavLink } from 'react-router-dom'
import { useLang } from '../i18n.jsx'

const LANGS = ['ru', 'kk', 'en']

export default function Header() {
  const { lang, setLang, t } = useLang()

  function linkClass({ isActive }) {
    return `whitespace-nowrap inline-flex min-h-11 items-center rounded-lg px-3 py-2 text-base ${isActive ? 'bg-brand-100 font-medium text-brand-700' : 'text-slate-600 hover:bg-slate-100'}`
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
          <div className="ml-2 flex overflow-hidden rounded-lg border border-slate-200">
            {LANGS.map((code) => (
              <button
                key={code}
                onClick={() => setLang(code)}
                aria-label={code}
                className={`min-h-11 min-w-11 px-3 py-2 text-sm uppercase ${lang === code ? 'bg-brand-600 text-white' : 'text-slate-600'}`}
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
