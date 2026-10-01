import { Link } from 'react-router-dom'
import { Card } from '../components/ui.jsx'

export default function NotFoundPage() {
  return (
    <Card>
      <h1 className="text-lg font-semibold">Page not found</h1>
      <Link to="/" className="mt-2 inline-block text-brand-600 underline">
        Back to start
      </Link>
    </Card>
  )
}
