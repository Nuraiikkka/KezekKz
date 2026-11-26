import { useEffect, useState } from 'react'
import { Link, NavLink, useNavigate } from 'react-router-dom'
import { useLang } from '../i18n.jsx'

const LANGS = ['ru', 'kk', 'en']

function hasToken() {
  try {
    return Boolean(localStorage.getItem('staffToken'))
  } catch {
    return false
  }
}

export default function StaffHeader() {
  const { lang, setLang, t } = useLang()
  const navigate = useNavigate()
  const [loggedIn, setLoggedIn] = useState(hasToken)

  useEffect(() => {
    function refresh() {
      setLoggedIn(hasToken())
    }
    window.addEventListener('staff-auth', refresh)
    return () => window.removeEventListener('staff-auth', refresh)
  }, [])

  function linkClass({ isActive }) {
    return `whitespace-nowrap rounded-lg px-2.5 py-1.5 text-sm ${
      isActive ? 'bg-white/20 font-medium text-white' : 'text-brand-100 hover:bg-white/10'
    }`
  }

  function logout() {
    try {
      localStorage.removeItem('staffToken')
    } catch {
      setLoggedIn(false)
    }
    setLoggedIn(false)
    window.dispatchEvent(new Event('staff-auth'))
    navigate('/staff')
    window.location.reload()
  }

  return (
    <header className="sticky top-0 z-10 bg-brand-900 text-white print:hidden">
      <div className="mx-auto flex max-w-3xl flex-wrap items-center justify-between gap-2 px-4 py-3">
        <Link to="/staff" className="flex items-center gap-2 text-lg font-semibold">
          <span className="flex h-8 w-8 items-center justify-center rounded-lg bg-white text-brand-700">K</span>
          KezekKz
          <span className="rounded-md bg-white/15 px-2 py-0.5 text-xs font-medium uppercase tracking-wide">{t('nav.badge')}</span>
        </Link>
        <nav className="flex flex-wrap items-center gap-1">
          {loggedIn && (
            <>
              <NavLink to="/staff" end className={linkClass}>
                {t('nav.queue')}
              </NavLink>
              <NavLink to="/staff/patients" className={linkClass}>
                {t('s.patients')}
              </NavLink>
              <NavLink to="/staff/stats" className={linkClass}>
                {t('s.stats')}
              </NavLink>
              <NavLink to="/board" className={linkClass}>
                {t('nav.board')}
              </NavLink>
              <NavLink to="/qr" className={linkClass}>
                {t('s.qr')}
              </NavLink>
            </>
          )}
          <div className="ml-2 flex overflow-hidden rounded-lg border border-white/30 text-xs">
            {LANGS.map((code) => (
              <button
                key={code}
                onClick={() => setLang(code)}
                className={`px-2 py-1 uppercase ${lang === code ? 'bg-white text-brand-900' : 'text-white'}`}
              >
                {code}
              </button>
            ))}
          </div>
          {loggedIn && (
            <button onClick={logout} className="ml-1 rounded-lg px-2.5 py-1.5 text-sm text-brand-100 hover:bg-white/10">
              {t('nav.logout')}
            </button>
          )}
        </nav>
      </div>
    </header>
  )
}
