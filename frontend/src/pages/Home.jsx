import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api, { getErrorText } from '../api.js'

export default function Home() {
  const [clinics, setClinics] = useState([])
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get('/clinics/')
      .then((response) => setClinics(response.data))
      .catch((err) => setError(getErrorText(err)))
  }, [])

  return (
    <div>
      <h1 className="text-2xl font-semibold">Book a visit without waiting in the hallway</h1>
      <p className="mt-1 text-slate-600">
        Answer a few short questions, see which doctor you need and how long you will wait.
      </p>

      {error && <p className="mt-4 text-red-600">{error}</p>}

      {clinics.map((clinic) => (
        <div key={clinic.id} className="mt-4 flex items-center justify-between rounded-xl bg-white p-4 shadow-sm">
          <div>
            <div className="font-medium">{clinic.name}</div>
            <div className="text-sm text-slate-500">{clinic.address}</div>
          </div>
          <Link to={`/clinics/${clinic.slug}/questions`} className="rounded-lg bg-brand-600 px-4 py-2 text-white">
            Start booking
          </Link>
        </div>
      ))}
    </div>
  )
}
