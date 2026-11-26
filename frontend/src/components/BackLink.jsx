import { useNavigate } from 'react-router-dom'
import { useLang } from '../i18n.jsx'

export default function BackLink({ to = '/' }) {
  const navigate = useNavigate()
  const { t } = useLang()

  function back() {
    if (window.history.length > 1) {
      navigate(-1)
    } else {
      navigate(to)
    }
  }

  return (
    <button type="button" onClick={back} className="mb-3 text-sm text-slate-500 hover:text-slate-800 print:hidden">
      ← {t('back')}
    </button>
  )
}
