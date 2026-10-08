import { Route, Routes } from 'react-router-dom'
import Header from './components/Header.jsx'
import Booking from './pages/Booking.jsx'
import Home from './pages/Home.jsx'
import Questions from './pages/Questions.jsx'
import Track from './pages/Track.jsx'

export default function App() {
  return (
    <div className="min-h-screen">
      <Header />
      <main className="mx-auto max-w-2xl px-4 py-6">
        <Routes>
          <Route path="/" element={<Home />} />
          <Route path="/clinics/:slug/questions" element={<Questions />} />
          <Route path="/clinics/:slug/booking" element={<Booking />} />
          <Route path="/track/:token" element={<Track />} />
          <Route path="*" element={<Home />} />
        </Routes>
      </main>
      <p className="py-4 text-center text-xs text-slate-400">
        KezekKz only gives suggestions. In an emergency call 103.
      </p>
    </div>
  )
}
