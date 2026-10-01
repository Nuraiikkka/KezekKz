import { Route, Routes } from 'react-router-dom'
import Layout from './components/Layout.jsx'
import BookingPage from './pages/BookingPage.jsx'
import HomePage from './pages/HomePage.jsx'
import IntakePage from './pages/IntakePage.jsx'
import NotFoundPage from './pages/NotFoundPage.jsx'
import TrackPage from './pages/TrackPage.jsx'

export default function App() {
  return (
    <Routes>
      <Route element={<Layout />}>
        <Route index element={<HomePage />} />
        <Route path="clinics/:slug/intake" element={<IntakePage />} />
        <Route path="clinics/:slug/book" element={<BookingPage />} />
        <Route path="track/:token" element={<TrackPage />} />
        <Route path="*" element={<NotFoundPage />} />
      </Route>
    </Routes>
  )
}
