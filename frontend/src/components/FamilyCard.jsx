import { useState } from 'react'
import api, { getErrorText } from '../api.js'
import { useLang } from '../i18n.jsx'

const RELATIONS = ['child', 'parent', 'spouse', 'other']

export default function FamilyCard({ family, token, onChange }) {
  const { t } = useLang()
  const [form, setForm] = useState({ full_name: '', birth_date: '', relation: 'child' })
  const [error, setError] = useState('')
  const header = { headers: { 'X-Patient-Token': token } }

  function add(event) {
    event.preventDefault()
    setError('')
    api
      .post('/patient/family/', { ...form, full_name: form.full_name.trim() }, header)
      .then((response) => {
        onChange([...family, response.data])
        setForm({ full_name: '', birth_date: '', relation: 'child' })
      })
      .catch((err) => setError(getErrorText(err)))
  }

  function remove(id) {
    api
      .delete(`/patient/family/${id}/`, header)
      .then(() => onChange(family.filter((item) => item.id !== id)))
      .catch((err) => setError(getErrorText(err)))
  }

  return (
    <div className="card mt-4">
      <h2 className="mb-1 font-medium">{t('fam.title')}</h2>
      <p className="mb-3 text-sm text-slate-500">{t('fam.hint')}</p>

      {family.length === 0 && <p className="mb-3 text-sm text-slate-500">{t('fam.none')}</p>}
      <ul className="mb-3 space-y-2">
        {family.map((member) => (
          <li key={member.id} className="flex items-center justify-between gap-2 rounded-xl bg-slate-50 px-3 py-2 text-sm">
            <span>
              <span className="font-medium">{member.full_name}</span>{' '}
              <span className="text-slate-500">
                · {t('rel.' + member.relation)} · {member.age} {t('fam.years')}
              </span>
            </span>
            <button type="button" onClick={() => remove(member.id)} className="text-slate-500 underline">
              {t('fam.remove')}
            </button>
          </li>
        ))}
      </ul>

      <form onSubmit={add} className="grid gap-2 sm:grid-cols-2">
        <input
          className="input sm:col-span-2"
          aria-label={t('fam.name')}
          placeholder={t('fam.name')}
          value={form.full_name}
          onChange={(event) => setForm({ ...form, full_name: event.target.value })}
        />
        <label className="text-sm text-slate-600">
          {t('fam.birth')}
          <input
            className="input mt-1"
            type="date"
            max={new Date().toISOString().slice(0, 10)}
            value={form.birth_date}
            onChange={(event) => setForm({ ...form, birth_date: event.target.value })}
          />
        </label>
        <label className="text-sm text-slate-600">
          {t('fam.relation')}
          <select className="input mt-1" value={form.relation} onChange={(event) => setForm({ ...form, relation: event.target.value })}>
            {RELATIONS.map((code) => (
              <option key={code} value={code}>
                {t('rel.' + code)}
              </option>
            ))}
          </select>
        </label>
        {error && <p className="text-sm text-red-600 sm:col-span-2">{error}</p>}
        <button disabled={form.full_name.trim().length < 2 || !form.birth_date} className="btn sm:col-span-2">
          {t('fam.add')}
        </button>
      </form>
    </div>
  )
}
