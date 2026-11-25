import { useLang } from '../i18n.jsx'

export default function Steps({ current }) {
  const { t } = useLang()
  const names = [t('b.step1'), t('b.step2'), t('b.step3')]

  return (
    <div className="mb-5 flex items-center gap-2">
      {names.map((name, index) => (
        <div key={name} className="flex flex-1 items-center gap-2">
          <div
            className={`flex h-7 w-7 shrink-0 items-center justify-center rounded-full text-sm font-semibold ${
              index <= current ? 'bg-brand-600 text-white' : 'bg-slate-200 text-slate-500'
            }`}
          >
            {index < current ? '✓' : index + 1}
          </div>
          <span className={`hidden text-sm sm:block ${index <= current ? 'font-medium' : 'text-slate-400'}`}>{name}</span>
          {index < names.length - 1 && <div className={`h-0.5 flex-1 ${index < current ? 'bg-brand-600' : 'bg-slate-200'}`} />}
        </div>
      ))}
    </div>
  )
}
