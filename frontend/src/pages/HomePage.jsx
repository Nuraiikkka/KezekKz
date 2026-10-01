import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { parseApiError } from '../api/client.js'
import { getClinics } from '../api/kezek.js'
import { Card, ErrorBox, Spinner } from '../components/ui.jsx'

export default function HomePage() {
  const [clinics, setClinics] = useState(null)
  const [error, setError] = useState('')

  const load = () =>
    getClinics()
      .then((data) => {
        setClinics(data)
        setError('')
      })
      .catch((e) => setError(parseApiError(e).message))

  useEffect(() => {
    load()
  }, [])

  return (
    <div className="space-y-5">
      <div>
        <h1 className="text-2xl font-semibold">Book a visit without waiting in the hallway</h1>
        <p className="mt-1 text-slate-600">
          Answer a few short questions, get matched to the right specialist and see your estimated wait time live.
        </p>
      </div>

      <ErrorBox message={error} onRetry={load} />
      {!clinics && !error && <Spinner />}

      {clinics?.length === 0 && <Card>No clinics are available yet.</Card>}

      <div className="space-y-3">
        {clinics?.map((clinic) => (
          <Card key={clinic.id} className="flex items-center justify-between gap-4">
            <div>
              <div className="font-medium">{clinic.name}</div>
              {clinic.address && <div className="text-sm text-slate-500">{clinic.address}</div>}
            </div>
            <Link
              to={`/clinics/${clinic.slug}/intake`}
              className="shrink-0 rounded-xl bg-brand-600 px-4 py-2.5 text-sm font-medium text-white hover:bg-brand-700"
            >
              Start booking
            </Link>
          </Card>
        ))}
      </div>
    </div>
  )
}
