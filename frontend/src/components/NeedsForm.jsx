import { useLang } from '../i18n.jsx'

const FLAGS = ['wheelchair', 'escort', 'interpreter']
const LANGUAGES = ['', 'ru', 'kk', 'en']

export default function NeedsForm({ value, onChange }) {
  const { t } = useLang()
  return (
    <fieldset className="card mt-4">
      <legend className="sr-only">{t('need.title')}</legend>
      <h2 className="mb-1 text-lg font-semibold">{t('need.title')}</h2>
      <p className="mb-3 text-sm text-slate-500">{t('need.hint')}</p>
      {FLAGS.map((flag) => (
        <label key={flag} className="mb-2 flex items-center gap-3 rounded-xl border border-slate-200 p-3 text-sm">
          <input
            type="checkbox"
            className="accent-emerald-700"
            checked={!!value[flag]}
            onChange={(event) => onChange({ ...value, [flag]: event.target.checked })}
          />
          {t('need.' + flag)}
        </label>
      ))}
      <label htmlFor="doctor-language" className="mt-3 block text-sm font-medium">
        {t('need.language')}
      </label>
      <select
        id="doctor-language"
        className="input mt-1"
        value={value.language || ''}
        onChange={(event) => onChange({ ...value, language: event.target.value })}
      >
        {LANGUAGES.map((code) => (
          <option key={code} value={code}>
            {t('need.lang_' + (code || 'any'))}
          </option>
        ))}
      </select>
    </fieldset>
  )
}
