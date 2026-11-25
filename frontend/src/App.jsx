import { Route, Routes } from 'react-router-dom'
import Header from './components/Header.jsx'
import { useLang } from './i18n.jsx'
import Board from './pages/Board.jsx'
import Booking from './pages/Booking.jsx'
import Home from './pages/Home.jsx'
import MyVisits from './pages/MyVisits.jsx'
import QrPoster from './pages/QrPoster.jsx'
import Questions from './pages/Questions.jsx'
import Staff from './pages/Staff.jsx'
import Stats from './pages/Stats.jsx'
import Track from './pages/Track.jsx'

export default function App() {
  const { t } = useLang()

  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-3xl px-4 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/clinics/:slug/questions" element={<Questions />} />
          <Route path="/clinics/:slug/booking" element={<Booking />} />
          <Route path="/track/:token" element={<Track />} />
          <Route path="/my" element={<MyVisits />} />
          <Route path="/staff" element={<Staff />} />
          <Route path="/staff/stats" element={<Stats />} />
          <Route path="/board" element={<Board />} />
          <Route path="/qr" element={<QrPoster />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </main>
      <p className="px-4 py-6 text-center text-xs text-slate-400 print:hidden">{t('footer')}
        <br />
        {t('footer2')}
      </p>
    </div>
  )
}
