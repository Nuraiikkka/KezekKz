import { Link, Outlet } from 'react-router-dom'

export default function Layout() {
  return (
    <div className="min-h-screen flex flex-col">
      <header className="bg-white border-b border-slate-200">
        <div className="mx-auto max-w-2xl px-4 py-3 flex items-center justify-between">
          <Link to="/" className="text-lg font-semibold text-brand-700">
            Kezek<span className="text-slate-400">Kz</span>
          </Link>
          <span className="text-xs text-slate-500">Smart patient queue</span>
        </div>
      </header>
      <main className="flex-1 mx-auto w-full max-w-2xl px-4 py-6">
        <Outlet />
      </main>
      <footer className="py-4 text-center text-xs text-slate-400">
        KezekKz gives routing suggestions only and never makes medical decisions.
        In an emergency call <strong>103</strong>.
      </footer>
    </div>
  )
}
