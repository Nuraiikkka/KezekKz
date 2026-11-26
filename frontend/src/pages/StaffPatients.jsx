import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import api from '../api.js'
import BackLink from '../components/BackLink.jsx'
import EmptyState from '../components/EmptyState.jsx'
import { useLang } from '../i18n.jsx'

export default function StaffPatients() {
  const { t } = useLang()
  const [query, setQuery] = useState('')
  const [list, setList] = useState([])
  const [denied, setDenied] = useState(false)

  useEffect(() => {
    const token = localStorage.getItem('staffToken')
    api
      .get(`/staff/patients/?q=${encodeURIComponent(query)}`, { headers: { Authorization: `Token ${token}` } })
      .then((response) => setList(response.data))
      .catch(() => setDenied(true))
  }, [query])

  if (denied) {
    return <EmptyState title={t('nf.staff')} text={t('nf.stafftext')} to="/staff" action={t('nf.stafflogin')} />
  }

  return (
    <div>
      <BackLink to="/staff" />
      <div className="flex items-center justify-between">
        <h1 className="text-2xl font-semibold">{t('s.patients')}</h1>
        <Link to="/staff" className="text-sm text-slate-500 underline">
          {t('sc.back')}
        </Link>
      </div>
      <input className="input mt-4" placeholder={t('s.search')} value={query} onChange={(event) => setQuery(event.target.value)} />
      <div className="mt-4 space-y-2">
        {list.map((patient) => (
          <Link key={patient.id} to={`/staff/patients/${patient.id}`} className="card flex items-center justify-between hover:border-brand-200">
            <span className="font-medium">{patient.full_name}</span>
            <span className="text-sm text-slate-500">{patient.phone}</span>
          </Link>
        ))}
      </div>
    </div>
  )
}
