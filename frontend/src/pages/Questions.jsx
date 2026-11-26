import { useEffect, useState } from 'react'
import { useNavigate, useParams, useSearchParams } from 'react-router-dom'
import api, { getErrorText } from '../api.js'
import EmptyState from '../components/EmptyState.jsx'
import Steps from '../components/Steps.jsx'
import { useLang } from '../i18n.jsx'

const RED_KEY = 'kezek-answers-'

function loadAnswers(slug) {
  try {
    return JSON.parse(sessionStorage.getItem(RED_KEY + slug)) || {}
  } catch {
    return {}
  }
}

function isEmpty(value) {
  return value === undefined || value === null || value === '' || (Array.isArray(value) && value.length === 0)
}

export default function Questions() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { t } = useLang()
  const [params, setParams] = useSearchParams()
  const [questions, setQuestions] = useState([])
  const [answers, setAnswers] = useState(() => loadAnswers(slug))
  const [agreed, setAgreed] = useState(false)
  const [error, setError] = useState('')
  const [missing, setMissing] = useState(false)

  useEffect(() => {
    api
      .get(`/intake/questions/?clinic=${slug}`)
      .then((response) => setQuestions(response.data))
      .catch((err) => {
        if (err.response && err.response.status === 404) setMissing(true)
        else setError(getErrorText(err))
      })
  }, [slug])

  useEffect(() => {
    try {
      sessionStorage.setItem(RED_KEY + slug, JSON.stringify(answers))
    } catch {
      return
    }
  }, [answers, slug])

  if (missing) {
    return <EmptyState title={t('nf.clinic')} text={t('nf.clinictext')} to="/" action={t('nf.home')} />
  }

  if (questions.length === 0) {
    return <p className="text-slate-500">{error || t('loading')}</p>
  }

  const requested = Number(params.get('step')) || 0
  const step = Math.min(Math.max(requested, 0), questions.length - 1)

  function goTo(next) {
    setParams({ step: String(next) })
  }

  const question = questions[step]
  const value = answers[question.key]
  const isLast = step === questions.length - 1
  const followup = question.followup
  const showFollowup = followup && (followup.when === null || followup.when.includes(value))
  const followupValue = followup ? answers[followup.key] : ''

  const options =
    question.options_by && answers[question.depends_on] && question.options_by[answers[question.depends_on]]
      ? question.options_by[answers[question.depends_on]]
      : question.options

  const answered = !question.required || !isEmpty(value)
  const followupOk = !showFollowup || !followup.required || !isEmpty(followupValue?.trim())
  const canGo = answered && followupOk
  const redFlagChosen = (answers.red_flags || []).some((flag) => flag !== 'none')

  function setAnswer(key, newValue) {
    const next = { ...answers, [key]: newValue }
    if (key === 'preferred_specialty') next.symptoms = []
    setAnswers(next)
  }

  function toggle(option) {
    let list = value || []
    if (option === 'none') {
      list = ['none']
    } else if (list.includes(option)) {
      list = list.filter((item) => item !== option)
    } else {
      list = [...list.filter((item) => item !== 'none'), option]
    }
    setAnswer(question.key, list)
  }

  function label(option) {
    if (question.key === 'symptoms') return t('sym.' + option.value, option.value)
    return t('o.' + option.value, option.label)
  }

  function back() {
    if (step === 0) {
      navigate('/')
    } else {
      navigate(-1)
    }
  }

  function send() {
    setError('')
    const clean = { ...answers }
    questions.forEach((item) => {
      if (item.followup && item.followup.when && !item.followup.when.includes(clean[item.key])) {
        delete clean[item.followup.key]
      }
    })
    Object.keys(clean).forEach((key) => {
      if (clean[key] === '' || (typeof clean[key] === 'string' && !clean[key].trim())) delete clean[key]
    })
    api
      .post('/intake/', { clinic: slug, answers: clean })
      .then((response) => {
        try {
          sessionStorage.setItem('kezek-intake-' + slug, JSON.stringify(response.data))
          sessionStorage.removeItem(RED_KEY + slug)
        } catch {
          setError('')
        }
        navigate(`/clinics/${slug}/booking`, { state: response.data })
      })
      .catch((err) => setError(getErrorText(err)))
  }

  function optionClass(selected) {
    return `mb-2 flex cursor-pointer items-center gap-3 rounded-xl border p-3 transition ${
      selected ? 'border-brand-500 bg-brand-50 font-medium' : 'border-slate-200 hover:bg-slate-50'
    }`
  }

  function placeholder() {
    if (followup.key === 'reason_text') return t('q.other_ph')
    if (followup.key === 'conditions_text') return t('q.cond_ph')
    return t('q.sym_ph')
  }

  return (
    <div>
      <Steps current={0} />

      <div className="mb-2 h-2 overflow-hidden rounded-full bg-slate-200">
        <div className="h-full bg-brand-500 transition-all" style={{ width: `${((step + (canGo ? 1 : 0)) / questions.length) * 100}%` }} />
      </div>
      <p className="text-sm text-slate-500">
        {t('q.step')} {step + 1} {t('q.of')} {questions.length}
      </p>

      <div className="card mt-3">
        <h2 className="mb-4 text-lg font-semibold">{t('question.' + question.key, question.text)}</h2>

        {question.type === 'single_choice' &&
          options.map((option) => (
            <label key={option.value} className={optionClass(value === option.value)}>
              <input
                type="radio"
                className="accent-emerald-700"
                checked={value === option.value}
                onChange={() => setAnswer(question.key, option.value)}
              />
              {label(option)}
            </label>
          ))}

        {question.type === 'multi_choice' && (
          <>
            {question.key === 'symptoms' && <p className="mb-3 text-sm text-slate-500">{t('q.sym_hint')}</p>}
            {question.key === 'red_flags' && <p className="mb-3 text-sm text-slate-500">{t('q.red_hint')}</p>}
            {question.key === 'red_flags' && redFlagChosen && (
              <div role="alert" className="mb-3 rounded-xl bg-red-600 p-3 font-medium text-white">
                {t('b.emergency')}
              </div>
            )}
            {options.map((option) => (
              <label key={option.value} className={optionClass((value || []).includes(option.value))}>
                <input
                  type="checkbox"
                  className="accent-emerald-700"
                  checked={(value || []).includes(option.value)}
                  onChange={() => toggle(option.value)}
                />
                {label(option)}
              </label>
            ))}
          </>
        )}

        {question.type === 'scale' && (
          <>
            <div className="flex gap-2">
              {[1, 2, 3, 4, 5].map((number) => (
                <button
                  key={number}
                  onClick={() => setAnswer(question.key, number)}
                  className={`h-14 flex-1 rounded-xl border text-lg font-medium transition ${
                    value === number ? 'border-brand-600 bg-brand-600 text-white' : 'border-slate-200 hover:bg-slate-50'
                  }`}
                >
                  {number}
                </button>
              ))}
            </div>
            <div className="mt-4 space-y-1 rounded-xl bg-slate-50 p-3 text-sm text-slate-600">
              <p>{t('scale.low')}</p>
              <p>{t('scale.mid')}</p>
              <p>{t('scale.high')}</p>
            </div>
          </>
        )}

        {showFollowup && (
          <textarea
            aria-label={t('question.' + question.key, question.text)}
            className="input mt-3"
            rows={3}
            maxLength={500}
            placeholder={placeholder()}
            value={followupValue || ''}
            onChange={(event) => setAnswer(followup.key, event.target.value)}
          />
        )}
      </div>

      {isLast && (
        <label className="card mt-3 flex items-start gap-2 text-sm text-slate-600">
          <input
            type="checkbox"
            className="mt-1 accent-emerald-700"
            checked={agreed}
            onChange={(event) => setAgreed(event.target.checked)}
          />
          <span>
            <span className="block font-medium text-slate-800">{t('q.consent_title')}</span>
            {t('b.consent')}
            <span className="block text-xs text-slate-500">{t('b.privacy')}</span>
          </span>
        </label>
      )}

      {error && <p className="mt-3 text-red-600">{error}</p>}

      <div className="mt-4 flex justify-between">
        <button onClick={back} className="btn-light">
          {step === 0 ? t('q.home') : t('back')}
        </button>
        {isLast ? (
          <button disabled={!canGo || !agreed} onClick={send} className="btn">
            {t('q.send')}
          </button>
        ) : (
          <button disabled={!canGo} onClick={() => goTo(step + 1)} className="btn">
            {t('next')}
          </button>
        )}
      </div>
    </div>
  )
}
