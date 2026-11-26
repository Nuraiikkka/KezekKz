import { useEffect } from 'react'
import { Route, Routes, useLocation } from 'react-router-dom'
import EmptyState from './components/EmptyState.jsx'
import Header from './components/Header.jsx'
import StaffHeader from './components/StaffHeader.jsx'
import { useLang } from './i18n.jsx'
import Board from './pages/Board.jsx'
import Booking from './pages/Booking.jsx'
import Home from './pages/Home.jsx'
import MyVisits from './pages/MyVisits.jsx'
import QrPoster from './pages/QrPoster.jsx'
import Questions from './pages/Questions.jsx'
import Staff from './pages/Staff.jsx'
import StaffPatient from './pages/StaffPatient.jsx'
import StaffPatients from './pages/StaffPatients.jsx'
import Stats from './pages/Stats.jsx'
import Track from './pages/Track.jsx'

export default function App() {
  const { t } = useLang()
  const { pathname } = useLocation()
  const staffArea = pathname.startsWith('/staff') || pathname === '/qr'

  useEffect(() => {
    const titles = [
      ['/clinics/', t('nav.book', 'Запись')],
      ['/track/', t('nav.track', 'Моя запись')],
      ['/my', t('nav.visits')],
      ['/board', t('board.title')],
      ['/staff', t('nav.badge')],
      ['/qr', 'QR'],
    ]
    const found = titles.find(([prefix]) => pathname.startsWith(prefix))
    document.title = found ? `${found[1]} · KezekKz` : t('seo.home')
    const description = document.querySelector('meta[name="description"]')
    if (description) description.setAttribute('content', t('seo.desc'))
  }, [pathname, t])

  return (
    <div className="min-h-screen">
      {staffArea ? <StaffHeader /> : <Header />}
      <main className="mx-auto max-w-3xl px-4 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/clinics/:slug/questions" element={<Questions />} />
          <Route path="/clinics/:slug/booking" element={<Booking />} />
          <Route path="/track/:token" element={<Track />} />
          <Route path="/my" element={<MyVisits />} />
          <Route path="/staff" element={<Staff />} />
          <Route path="/staff/stats" element={<Stats />} />
          <Route path="/staff/patients" element={<StaffPatients />} />
          <Route path="/staff/patients/:id" element={<StaffPatient />} />
          <Route path="/board" element={<Board />} />
          <Route path="/qr" element={<QrPoster />} />
          <Route path="*" element={<EmptyState title={t('nf.title')} text={t('nf.text')} to="/" action={t('nf.home')} />} />
        </Routes>
      </main>
      <p className="px-4 py-6 text-center text-sm text-slate-600 print:hidden"><strong className="font-semibold text-slate-800">{t('footer')}</strong>
        <br />
        {t('footer2')}
      </p>
    </div>
  )
}
