import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import { parseApiError } from '../api/client.js'
import { getQuestions, submitIntake } from '../api/kezek.js'
import { Button, Card, ErrorBox, Spinner } from '../components/ui.jsx'
import { intakeStorageKey } from '../utils/storage.js'

function isAnswered(question, value) {
  if (!question.required) return true
  if (Array.isArray(value)) return value.length > 0
  return value !== undefined && value !== null && value !== ''
}

function QuestionInput({ question, value, onChange }) {
  if (question.type === 'single_choice') {
    return (
      <div className="grid gap-2">
        {question.options.map((opt) => (
          <label
            key={opt.value}
            className={`flex cursor-pointer items-center gap-3 rounded-xl px-4 py-3 ring-1 transition ${
              value === opt.value ? 'bg-brand-50 ring-brand-500' : 'ring-slate-200 hover:bg-slate-50'
            }`}
          >
            <input
              type="radio"
              name={question.key}
              className="accent-brand-600"
              checked={value === opt.value}
              onChange={() => onChange(opt.value)}
            />
            {opt.label}
          </label>
        ))}
      </div>
    )
  }

  if (question.type === 'multi_choice') {
    const selected = value || []
    const toggle = (v) => {
      if (v === 'none') return onChange(selected.includes('none') ? [] : ['none'])
      const withoutNone = selected.filter((s) => s !== 'none')
      onChange(withoutNone.includes(v) ? withoutNone.filter((s) => s !== v) : [...withoutNone, v])
    }
    return (
      <div className="grid gap-2">
        {question.options.map((opt) => (
          <label
            key={opt.value}
            className={`flex cursor-pointer items-center gap-3 rounded-xl px-4 py-3 ring-1 transition ${
              selected.includes(opt.value) ? 'bg-brand-50 ring-brand-500' : 'ring-slate-200 hover:bg-slate-50'
            }`}
          >
            <input
              type="checkbox"
              className="accent-brand-600"
              checked={selected.includes(opt.value)}
              onChange={() => toggle(opt.value)}
            />
            {opt.label}
          </label>
        ))}
      </div>
    )
  }

  if (question.type === 'scale') {
    const values = Array.from({ length: question.max - question.min + 1 }, (_, i) => question.min + i)
    return (
      <div>
        <div className="flex gap-2">
          {values.map((n) => (
            <button
              key={n}
              type="button"
              onClick={() => onChange(n)}
              className={`h-12 flex-1 rounded-xl text-lg font-semibold ring-1 transition ${
                value === n ? 'bg-brand-600 text-white ring-brand-600' : 'ring-slate-200 hover:bg-slate-50'
              }`}
            >
              {n}
            </button>
          ))}
        </div>
        <div className="mt-1 flex justify-between text-xs text-slate-500">
          <span>Mild</span>
          <span>Severe</span>
        </div>
      </div>
    )
  }

  return (
    <div>
      <textarea
        rows={3}
        maxLength={question.max_length}
        value={value || ''}
        onChange={(e) => onChange(e.target.value)}
        className="w-full rounded-xl p-3 ring-1 ring-slate-200 focus:outline-none focus:ring-brand-500"
        placeholder="Optional"
      />
      {question.persisted === false && (
        <p className="mt-1 text-xs text-slate-500">
          Shown to the system only for this request — we never store health information.
        </p>
      )}
    </div>
  )
}

export default function IntakePage() {
  const { slug } = useParams()
  const navigate = useNavigate()
  const [questions, setQuestions] = useState(null)
  const [step, setStep] = useState(0)
  const [answers, setAnswers] = useState({})
  const [error, setError] = useState('')
  const [submitting, setSubmitting] = useState(false)

  const load = () =>
    getQuestions()
      .then((data) => {
        setQuestions(data.questions)
        setError('')
      })
      .catch((e) => setError(parseApiError(e).message))
  useEffect(() => {
    load()
  }, [])

  if (!questions) {
    return error ? <ErrorBox message={error} onRetry={load} /> : <Spinner />
  }

  const question = questions[step]
  const isLast = step === questions.length - 1
  const value = answers[question.key]

  const submit = async () => {
    setSubmitting(true)
    setError('')
    try {
      const result = await submitIntake(slug, answers)
      sessionStorage.setItem(intakeStorageKey(slug), JSON.stringify(result))
      navigate(`/clinics/${slug}/book`, { state: { intake: result } })
    } catch (e) {
      const { message, fields } = parseApiError(e)
      const firstBad = questions.findIndex((q) => fields[q.key])
      if (firstBad >= 0) setStep(firstBad)
      setError(firstBad >= 0 ? fields[questions[firstBad].key] : message)
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="space-y-4">
      <div>
        <div className="flex justify-between text-xs text-slate-500">
          <span>
            Question {step + 1} of {questions.length}
          </span>
          <span>About your visit</span>
        </div>
        <div className="mt-2 h-1.5 rounded-full bg-slate-200">
          <div
            className="h-1.5 rounded-full bg-brand-500 transition-all"
            style={{ width: `${((step + 1) / questions.length) * 100}%` }}
          />
        </div>
      </div>

      <Card>
        <h2 className="mb-4 text-lg font-medium">{question.text}</h2>
        <QuestionInput
          question={question}
          value={value}
          onChange={(v) => setAnswers((prev) => ({ ...prev, [question.key]: v }))}
        />
      </Card>

      <ErrorBox message={error} />

      <div className="flex justify-between">
        <Button variant="secondary" disabled={step === 0} onClick={() => setStep(step - 1)}>
          Back
        </Button>
        {isLast ? (
          <Button disabled={!isAnswered(question, value) || submitting} onClick={submit}>
            {submitting ? 'Checking…' : 'See my suggestion'}
          </Button>
        ) : (
          <Button disabled={!isAnswered(question, value)} onClick={() => setStep(step + 1)}>
            Next
          </Button>
        )}
      </div>
    </div>
  )
}
