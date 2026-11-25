import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api, { getErrorText } from '../api.js'
import Steps from '../components/Steps.jsx'
import { useLang } from '../i18n.jsx'

export default function Questions() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const { t } = useLang()
  const [questions, setQuestions] = useState([])
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState({})
  const [error, setError] = useState('')

  useEffect(() => {
    api
      .get('/intake/questions/')
      .then((response) => setQuestions(response.data))
      .catch((err) => setError(getErrorText(err)))
  }, [])

  if (questions.length === 0) {
    return <p className="text-slate-500">{error || t('loading')}</p>
  }

  const question = questions[step]
  const value = answers[question.key]
  const isLast = step === questions.length - 1
  const isAnswered = !question.required || (value !== undefined && value !== '' && value.length !== 0)

  function setAnswer(newValue) {
    setAnswers({ ...answers, [question.key]: newValue })
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
    setAnswer(list)
  }

  function send() {
    setError('')
    api
      .post('/intake/', { clinic: slug, answers: answers })
      .then((response) => navigate(`/clinics/${slug}/booking`, { state: response.data }))
      .catch((err) => setError(getErrorText(err)))
  }

  function optionClass(selected) {
    return `mb-2 flex cursor-pointer items-center gap-3 rounded-xl border p-3 transition ${
      selected ? 'border-brand-500 bg-brand-50 font-medium' : 'border-slate-200 hover:bg-slate-50'
    }`
  }

  return (
    <div>
      <Steps current={0} />

      <div className="mb-2 h-2 overflow-hidden rounded-full bg-slate-200">
        <div className="h-full bg-brand-500 transition-all" style={{ width: `${((step + 1) / questions.length) * 100}%` }} />
      </div>
      <p className="text-sm text-slate-500">
        {t('q.step')} {step + 1} {t('q.of')} {questions.length}
      </p>

      <div className="card mt-3">
        <h2 className="mb-4 text-lg font-semibold">{t('question.' + question.key, question.text)}</h2>

        {question.type === 'single_choice' &&
          question.options.map((option) => (
            <label key={option.value} className={optionClass(value === option.value)}>
              <input
                type="radio"
                className="accent-emerald-700"
                checked={value === option.value}
                onChange={() => setAnswer(option.value)}
              />
              {t('o.' + option.value, option.label)}
            </label>
          ))}

        {question.type === 'multi_choice' &&
          question.options.map((option) => (
            <label key={option.value} className={optionClass((value || []).includes(option.value))}>
              <input
                type="checkbox"
                className="accent-emerald-700"
                checked={(value || []).includes(option.value)}
                onChange={() => toggle(option.value)}
              />
              {t('o.' + option.value, option.label)}
            </label>
          ))}

        {question.type === 'scale' && (
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((number) => (
              <button
                key={number}
                onClick={() => setAnswer(number)}
                className={`h-14 flex-1 rounded-xl border text-lg font-medium transition ${
                  value === number ? 'border-brand-600 bg-brand-600 text-white' : 'border-slate-200 hover:bg-slate-50'
                }`}
              >
                {number}
              </button>
            ))}
          </div>
        )}

        {question.type === 'text' && (
          <textarea
            className="input"
            rows={3}
            placeholder={t('q.optional')}
            value={value || ''}
            onChange={(event) => setAnswer(event.target.value)}
          />
        )}
      </div>

      {error && <p className="mt-3 text-red-600">{error}</p>}

      <div className="mt-4 flex justify-between">
        <button disabled={step === 0} onClick={() => setStep(step - 1)} className="btn-light">
          {t('back')}
        </button>
        {isLast ? (
          <button disabled={!isAnswered} onClick={send} className="btn">
            {t('q.send')}
          </button>
        ) : (
          <button disabled={!isAnswered} onClick={() => setStep(step + 1)} className="btn">
            {t('next')}
          </button>
        )}
      </div>
    </div>
  )
}
