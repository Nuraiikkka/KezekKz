import { useEffect, useState } from 'react'
import { useNavigate, useParams } from 'react-router-dom'
import api, { getErrorText } from '../api.js'

export default function Questions() {
  const { slug } = useParams()
  const navigate = useNavigate()
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
    return <p className="text-slate-500">{error || 'Loading...'}</p>
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

  return (
    <div>
      <p className="text-sm text-slate-500">
        Question {step + 1} of {questions.length}
      </p>

      <div className="mt-2 rounded-xl bg-white p-5 shadow-sm">
        <h2 className="mb-4 text-lg font-medium">{question.text}</h2>

        {question.type === 'single_choice' &&
          question.options.map((option) => (
            <label key={option.value} className="mb-2 flex items-center gap-3 rounded-lg border p-3">
              <input type="radio" checked={value === option.value} onChange={() => setAnswer(option.value)} />
              {option.label}
            </label>
          ))}

        {question.type === 'multi_choice' &&
          question.options.map((option) => (
            <label key={option.value} className="mb-2 flex items-center gap-3 rounded-lg border p-3">
              <input
                type="checkbox"
                checked={(value || []).includes(option.value)}
                onChange={() => toggle(option.value)}
              />
              {option.label}
            </label>
          ))}

        {question.type === 'scale' && (
          <div className="flex gap-2">
            {[1, 2, 3, 4, 5].map((number) => (
              <button
                key={number}
                onClick={() => setAnswer(number)}
                className={`h-12 flex-1 rounded-lg border text-lg ${value === number ? 'bg-brand-600 text-white' : ''}`}
              >
                {number}
              </button>
            ))}
          </div>
        )}

        {question.type === 'text' && (
          <textarea
            className="w-full rounded-lg border p-3"
            rows={3}
            placeholder="Optional. We don't save this answer."
            value={value || ''}
            onChange={(event) => setAnswer(event.target.value)}
          />
        )}
      </div>

      {error && <p className="mt-3 text-red-600">{error}</p>}

      <div className="mt-4 flex justify-between">
        <button disabled={step === 0} onClick={() => setStep(step - 1)} className="rounded-lg border px-4 py-2">
          Back
        </button>
        {isLast ? (
          <button disabled={!isAnswered} onClick={send} className="rounded-lg bg-brand-600 px-4 py-2 text-white disabled:opacity-50">
            See my suggestion
          </button>
        ) : (
          <button
            disabled={!isAnswered}
            onClick={() => setStep(step + 1)}
            className="rounded-lg bg-brand-600 px-4 py-2 text-white disabled:opacity-50"
          >
            Next
          </button>
        )}
      </div>
    </div>
  )
}
