import { useState } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const steps = [
  {
    key:         'name',
    question:    "What should Jarvis call you?",
    placeholder: 'Your first name',
    hint:        'Jarvis will use this when calling businesses on your behalf',
    type:        'text',
  },
  {
    key:         'location',
    question:    'Where are you located?',
    placeholder: 'e.g. Toronto, ON',
    hint:        'Used to find businesses near you',
    type:        'text',
  },
  {
    key:         'preferred_time',
    question:    'When do you prefer appointments?',
    placeholder: '',
    hint:        'Jarvis will try to book during this time by default',
    type:        'choice',
    options:     ['morning', 'afternoon', 'evening'],
  },
  {
    key:         'phone',
    question:    'Your phone number?',
    placeholder: '+1 416 555 0123',
    hint:        'Jarvis will call this number to confirm bookings',
    type:        'text',
  },
]

export default function OnboardingPage() {
  const navigate        = useNavigate()
  const [step, setStep] = useState(0)
  const [answers, setAnswers]   = useState({})
  const [value, setValue]       = useState('')
  const [saving, setSaving]     = useState(false)

  const current = steps[step]

  const handleNext = async () => {
    if (!value.trim() && current.type !== 'choice') return

    const updated = { ...answers, [current.key]: value }
    setAnswers(updated)
    setValue('')

    if (step < steps.length - 1) {
      setStep(step + 1)
      return
    }

    // Last step — save all to memory
    setSaving(true)
    try {
      const api = axios.create({
        baseURL: 'http://localhost:8000',
        headers: {
          'Content-Type':  'application/json',
          'Authorization': `Bearer ${localStorage.getItem('jarvis_token')}`,
        },
      })

      for (const [key, val] of Object.entries(updated)) {
        await api.post('/memory', { key, value: val })
      }

      // Mark onboarding complete
      localStorage.setItem('jarvis_onboarded', 'true')
      navigate('/dashboard')
    } catch (err) {
      console.error(err)
      navigate('/dashboard')
    } finally {
      setSaving(false)
    }
  }

  const handleChoice = async (choice) => {
    setValue(choice)
    const updated = { ...answers, [current.key]: choice }
    setAnswers(updated)
    setValue('')

    if (step < steps.length - 1) {
      setStep(step + 1)
    } else {
      setSaving(true)
      try {
        const api = axios.create({
          baseURL: 'http://localhost:8000',
          headers: {
            'Content-Type':  'application/json',
            'Authorization': `Bearer ${localStorage.getItem('jarvis_token')}`,
          },
        })
        for (const [key, val] of Object.entries(updated)) {
          await api.post('/memory', { key, value: val })
        }
        localStorage.setItem('jarvis_onboarded', 'true')
        navigate('/dashboard')
      } catch {
        navigate('/dashboard')
      } finally {
        setSaving(false)
      }
    }
  }

  return (
    <div className="min-h-screen bg-jarvis-bg flex items-center justify-center px-4">
      <div className="w-full max-w-lg">

        {/* Progress dots */}
        <div className="flex justify-center gap-2 mb-10">
          {steps.map((_, i) => (
            <div key={i} className={`h-1.5 rounded-full transition-all duration-300
              ${i === step ? 'w-8 bg-jarvis-accent' :
                i < step  ? 'w-4 bg-jarvis-accent/40' :
                             'w-4 bg-jarvis-border'}`}
            />
          ))}
        </div>

        {/* Card */}
        <div className="bg-jarvis-surface border border-jarvis-border rounded-2xl p-10 text-center">
          <div className="w-12 h-12 rounded-xl bg-jarvis-accent/20 border border-jarvis-accent/40 flex items-center justify-center mx-auto mb-6 animate-glow-pulse">
            {/* Replace the J div with actual logo */}
            <img
              src="/android-chrome-192x192.png"
              alt="Jarvis"
              className="w-12 h-12 rounded-xl object-cover mx-auto mb-6"
            />          
          </div>

          <h2 className="font-display text-3xl text-jarvis-text mb-2">
            {current.question}
          </h2>
          <p className="font-mono text-jarvis-muted text-xs mb-8">{current.hint}</p>

          {current.type === 'choice' ? (
            <div className="flex gap-3 justify-center flex-wrap">
              {current.options.map(opt => (
                <button
                  key={opt}
                  onClick={() => handleChoice(opt)}
                  className="border border-jarvis-border text-jarvis-sub font-mono text-sm
                             px-6 py-3 rounded-xl hover:border-jarvis-accent hover:text-jarvis-accent
                             transition-colors capitalize"
                >
                  {opt}
                </button>
              ))}
            </div>
          ) : (
            <div className="space-y-4">
              <input
                type={current.type}
                value={value}
                onChange={e => setValue(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleNext()}
                placeholder={current.placeholder}
                autoFocus
                className="w-full bg-jarvis-bg border border-jarvis-border rounded-xl
                           px-5 py-4 text-center text-jarvis-text font-body text-lg
                           placeholder:text-jarvis-muted outline-none
                           focus:border-jarvis-accent transition-colors"
              />
              <button
                onClick={handleNext}
                disabled={!value.trim() || saving}
                className="w-full bg-jarvis-accent text-white font-mono py-3 rounded-xl
                           hover:bg-jarvis-glow transition-colors disabled:opacity-30"
              >
                {saving ? 'saving...' : step === steps.length - 1 ? 'finish' : 'continue →'}
              </button>
            </div>
          )}

          {/* Skip */}
          <button
            onClick={() => {
              if (step < steps.length - 1) setStep(step + 1)
              else navigate('/dashboard')
            }}
            className="mt-4 font-mono text-jarvis-muted text-xs hover:text-jarvis-sub transition-colors"
          >
            skip for now
          </button>
        </div>

        <p className="text-center font-mono text-jarvis-muted text-xs mt-4">
          {step + 1} of {steps.length}
        </p>
      </div>
    </div>
  )
}