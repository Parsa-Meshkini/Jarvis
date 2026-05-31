import { useState, useEffect, useRef } from 'react'
import { useNavigate } from 'react-router-dom'
import axios from 'axios'

const steps = [
  {
    key:         'name',
    question:    "What should Jarvis call you?",
    placeholder: 'Your first name',
    hint:        'Jarvis will use this when calling businesses on your behalf',
    type:        'text',
    emoji:       '👋',
    accent:      '#6C63FF',
    glow:        'rgba(108,99,255,0.3)',
    bg:          'rgba(108,99,255,0.08)',
  },
  {
    key:         'location',
    question:    'Where are you located?',
    placeholder: 'e.g. Toronto, ON',
    hint:        'Used to find businesses near you on Google Maps',
    type:        'text',
    emoji:       '📍',
    accent:      '#06B6D4',
    glow:        'rgba(6,182,212,0.3)',
    bg:          'rgba(6,182,212,0.08)',
  },
  {
    key:         'preferred_time',
    question:    'When do you prefer appointments?',
    placeholder: '',
    hint:        'Jarvis will try to book during this window by default',
    type:        'choice',
    options:     ['morning', 'afternoon', 'evening'],
    emoji:       '🕐',
    accent:      '#F59E0B',
    glow:        'rgba(245,158,11,0.3)',
    bg:          'rgba(245,158,11,0.08)',
  },
  {
    key:         'phone',
    question:    'Your phone number?',
    placeholder: '+1 416 555 0123',
    hint:        'Jarvis calls this number to confirm your bookings',
    type:        'text',
    emoji:       '📞',
    accent:      '#10B981',
    glow:        'rgba(16,185,129,0.3)',
    bg:          'rgba(16,185,129,0.08)',
  },
]

function Particle({ style }) {
  return <div style={style} />
}

export default function OnboardingPage() {
  const navigate          = useNavigate()
  const [step, setStep]   = useState(0)
  const [answers, setAnswers] = useState({})
  const [value, setValue]     = useState('')
  const [saving, setSaving]   = useState(false)
  const [animating, setAnimating] = useState(false)
  const [particles, setParticles] = useState([])
  const inputRef = useRef(null)
  const currentUser = (() => {
    try {
      return JSON.parse(localStorage.getItem('jarvis_user') || 'null')
    } catch {
      return null
    }
  })()
  const onboardingKey = currentUser?.id ? `jarvis_onboarded_${currentUser.id}` : 'jarvis_onboarded'

  const current = steps[step]

  useEffect(() => {
    const p = Array.from({ length: 18 }, (_, i) => ({
      id: i,
      width:  Math.random() * 6 + 2,
      height: Math.random() * 6 + 2,
      left:   Math.random() * 100,
      top:    Math.random() * 100,
      delay:  Math.random() * 4,
      duration: Math.random() * 8 + 6,
      opacity: Math.random() * 0.4 + 0.1,
    }))
    setParticles(p)
  }, [])

  useEffect(() => {
    setTimeout(() => inputRef.current?.focus(), 300)
  }, [step])

  const advance = (newAnswers) => {
    setAnimating(true)
    setTimeout(() => {
      setStep(s => s + 1)
      setValue('')
      setAnimating(false)
    }, 250)
  }

  const handleNext = async () => {
    if (!value.trim()) return
    const updated = { ...answers, [current.key]: value }
    setAnswers(updated)
    if (step < steps.length - 1) {
      advance(updated)
      return
    }
    await save(updated)
  }

  const handleChoice = async (choice) => {
    const updated = { ...answers, [current.key]: choice }
    setAnswers(updated)
    if (step < steps.length - 1) {
      setAnimating(true)
      setTimeout(() => {
        setStep(s => s + 1)
        setValue('')
        setAnimating(false)
      }, 250)
      return
    }
    await save(updated)
  }

  const save = async (data) => {
    setSaving(true)
    try {
      const api = axios.create({
        baseURL: 'http://localhost:8000',
        headers: { 'Content-Type': 'application/json', 'Authorization': `Bearer ${localStorage.getItem('jarvis_token')}` },
      })
      for (const [k, v] of Object.entries(data)) {
        await api.post('/memory', { key: k, value: v })
      }
      localStorage.setItem(onboardingKey, 'true')
      navigate('/dashboard')
    } catch {
      navigate('/dashboard')
    } finally {
      setSaving(false)
    }
  }

  return (
    <div style={{
      minHeight: '100vh',
      background: '#0A0A0F',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      padding: '24px',
      position: 'relative',
      overflow: 'hidden',
    }}>

      {/* Animated background orbs */}
      <div style={{
        position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none',
      }}>
        <div style={{
          position: 'absolute',
          width: 600, height: 600,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${current.glow} 0%, transparent 70%)`,
          top: '-20%', left: '-10%',
          animation: 'orb1 12s ease-in-out infinite',
          transition: 'background 0.8s ease',
        }} />
        <div style={{
          position: 'absolute',
          width: 500, height: 500,
          borderRadius: '50%',
          background: `radial-gradient(circle, ${current.glow} 0%, transparent 70%)`,
          bottom: '-15%', right: '-5%',
          animation: 'orb2 15s ease-in-out infinite',
          transition: 'background 0.8s ease',
        }} />
        <div style={{
          position: 'absolute',
          width: 300, height: 300,
          borderRadius: '50%',
          background: `radial-gradient(circle, rgba(255,255,255,0.03) 0%, transparent 70%)`,
          top: '50%', left: '50%',
          transform: 'translate(-50%, -50%)',
          animation: 'orb3 8s ease-in-out infinite',
        }} />
      </div>

      {/* Floating particles */}
      {particles.map(p => (
        <div key={p.id} style={{
          position: 'absolute',
          width: p.width,
          height: p.height,
          borderRadius: '50%',
          background: current.accent,
          left: `${p.left}%`,
          top: `${p.top}%`,
          opacity: p.opacity,
          animation: `float ${p.duration}s ${p.delay}s ease-in-out infinite`,
          transition: 'background 0.8s ease',
          pointerEvents: 'none',
        }} />
      ))}

      {/* Grid pattern overlay */}
      <div style={{
        position: 'absolute', inset: 0,
        backgroundImage: `linear-gradient(${current.accent}08 1px, transparent 1px), linear-gradient(90deg, ${current.accent}08 1px, transparent 1px)`,
        backgroundSize: '60px 60px',
        transition: 'background-image 0.8s ease',
        pointerEvents: 'none',
      }} />

      <style>{`
        @keyframes orb1 { 0%,100% { transform: translate(0,0) scale(1); } 50% { transform: translate(60px,40px) scale(1.1); } }
        @keyframes orb2 { 0%,100% { transform: translate(0,0) scale(1); } 50% { transform: translate(-40px,-30px) scale(1.05); } }
        @keyframes orb3 { 0%,100% { transform: translate(-50%,-50%) scale(1); } 50% { transform: translate(-50%,-50%) scale(1.3); } }
        @keyframes float { 0%,100% { transform: translateY(0px) rotate(0deg); } 33% { transform: translateY(-20px) rotate(120deg); } 66% { transform: translateY(-10px) rotate(240deg); } }
        @keyframes slideIn { from { opacity: 0; transform: translateY(24px); } to { opacity: 1; transform: translateY(0); } }
        @keyframes slideOut { from { opacity: 1; transform: translateY(0); } to { opacity: 0; transform: translateY(-24px); } }
        @keyframes pulse-ring { 0% { transform: scale(1); opacity: 0.6; } 100% { transform: scale(1.8); opacity: 0; } }
        @keyframes shimmer { 0% { background-position: -200% 0; } 100% { background-position: 200% 0; } }
        .step-card { animation: slideIn 0.4s cubic-bezier(0.16,1,0.3,1) forwards; }
        .step-card-exit { animation: slideOut 0.25s ease forwards; }
        .choice-btn:hover { transform: translateY(-2px); }
        .continue-btn:hover { transform: translateY(-1px); box-shadow: 0 8px 30px var(--btn-shadow); }
        .continue-btn:active { transform: translateY(0); }
      `}</style>

      <div style={{ width: '100%', maxWidth: 480, position: 'relative', zIndex: 1 }}>

        {/* Top: logo + step counter */}
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: 32 }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
            <img src="/jarvis-logo.svg" alt="Jarvis" style={{ width: 32, height: 32, borderRadius: 8, objectFit: 'cover' }} />
            <span style={{ fontFamily: 'Syne, sans-serif', color: '#E2E2F0', fontSize: 18, fontWeight: 700 }}>Jarvis</span>
          </div>
          <span style={{ fontFamily: 'JetBrains Mono, monospace', color: '#4A4A6A', fontSize: 12 }}>
            {step + 1} / {steps.length}
          </span>
        </div>

        {/* Progress bar */}
        <div style={{ height: 2, background: '#1A1A2E', borderRadius: 2, marginBottom: 40, overflow: 'hidden' }}>
          <div style={{
            height: '100%',
            width: `${((step + 1) / steps.length) * 100}%`,
            background: `linear-gradient(90deg, ${current.accent}, ${current.accent}AA)`,
            borderRadius: 2,
            transition: 'width 0.5s cubic-bezier(0.16,1,0.3,1), background 0.8s ease',
            position: 'relative',
            overflow: 'hidden',
          }}>
            <div style={{
              position: 'absolute', inset: 0,
              background: 'linear-gradient(90deg, transparent, rgba(255,255,255,0.3), transparent)',
              backgroundSize: '200% 100%',
              animation: 'shimmer 2s infinite',
            }} />
          </div>
        </div>

        {/* Main card */}
        <div
          className={animating ? 'step-card-exit' : 'step-card'}
          style={{
            background: 'rgba(17,17,28,0.85)',
            backdropFilter: 'blur(20px)',
            border: `1px solid ${current.accent}30`,
            borderRadius: 24,
            padding: '48px 40px',
            textAlign: 'center',
            boxShadow: `0 0 60px ${current.glow}, 0 20px 60px rgba(0,0,0,0.5)`,
            transition: 'border-color 0.8s ease, box-shadow 0.8s ease',
          }}
        >
          {/* Emoji with pulse ring */}
          <div style={{ position: 'relative', display: 'inline-block', marginBottom: 28 }}>
            <div style={{
              position: 'absolute', inset: -8,
              borderRadius: '50%',
              border: `2px solid ${current.accent}60`,
              animation: 'pulse-ring 2.5s ease-out infinite',
            }} />
            <div style={{
              width: 72, height: 72,
              borderRadius: '50%',
              background: current.bg,
              border: `1.5px solid ${current.accent}50`,
              display: 'flex', alignItems: 'center', justifyContent: 'center',
              fontSize: 32,
              transition: 'background 0.8s ease, border-color 0.8s ease',
            }}>
              {current.emoji}
            </div>
          </div>

          {/* Question */}
          <h2 style={{
            fontFamily: 'Syne, sans-serif',
            fontSize: 28,
            fontWeight: 700,
            color: '#E2E2F0',
            marginBottom: 10,
            lineHeight: 1.2,
          }}>
            {current.question}
          </h2>

          {/* Hint */}
          <p style={{
            fontFamily: 'JetBrains Mono, monospace',
            fontSize: 12,
            color: '#4A4A6A',
            marginBottom: 36,
            lineHeight: 1.6,
          }}>
            {current.hint}
          </p>

          {/* Input or choice */}
          {current.type === 'choice' ? (
            <div style={{ display: 'flex', gap: 12, justifyContent: 'center', flexWrap: 'wrap' }}>
              {current.options.map(opt => (
                <button
                  key={opt}
                  className="choice-btn"
                  onClick={() => handleChoice(opt)}
                  style={{
                    border: `1.5px solid ${current.accent}40`,
                    background: current.bg,
                    color: '#E2E2F0',
                    fontFamily: 'JetBrains Mono, monospace',
                    fontSize: 13,
                    padding: '14px 28px',
                    borderRadius: 14,
                    cursor: 'pointer',
                    transition: 'all 0.2s ease',
                    textTransform: 'capitalize',
                  }}
                  onMouseEnter={e => {
                    e.target.style.borderColor = current.accent
                    e.target.style.background = `${current.accent}20`
                    e.target.style.color = current.accent
                  }}
                  onMouseLeave={e => {
                    e.target.style.borderColor = `${current.accent}40`
                    e.target.style.background = current.bg
                    e.target.style.color = '#E2E2F0'
                  }}
                >
                  {opt}
                </button>
              ))}
            </div>
          ) : (
            <div style={{ display: 'flex', flexDirection: 'column', gap: 14 }}>
              <input
                ref={inputRef}
                type={current.type}
                value={value}
                onChange={e => setValue(e.target.value)}
                onKeyDown={e => e.key === 'Enter' && handleNext()}
                placeholder={current.placeholder}
                style={{
                  width: '100%',
                  background: 'rgba(10,10,15,0.6)',
                  border: `1.5px solid ${value ? current.accent : '#2A2A3E'}`,
                  borderRadius: 14,
                  padding: '18px 20px',
                  textAlign: 'center',
                  color: '#E2E2F0',
                  fontSize: 18,
                  fontFamily: 'DM Sans, sans-serif',
                  outline: 'none',
                  transition: 'border-color 0.3s ease, box-shadow 0.3s ease',
                  boxShadow: value ? `0 0 20px ${current.glow}` : 'none',
                  boxSizing: 'border-box',
                }}
                onFocus={e => {
                  e.target.style.borderColor = current.accent
                  e.target.style.boxShadow = `0 0 20px ${current.glow}`
                }}
                onBlur={e => {
                  if (!value) {
                    e.target.style.borderColor = '#2A2A3E'
                    e.target.style.boxShadow = 'none'
                  }
                }}
              />
              <button
                className="continue-btn"
                onClick={handleNext}
                disabled={!value.trim() || saving}
                style={{
                  '--btn-shadow': current.glow,
                  width: '100%',
                  background: value.trim() ? current.accent : '#2A2A3E',
                  color: '#fff',
                  fontFamily: 'JetBrains Mono, monospace',
                  fontSize: 14,
                  padding: '16px',
                  borderRadius: 14,
                  border: 'none',
                  cursor: value.trim() ? 'pointer' : 'not-allowed',
                  opacity: saving ? 0.7 : 1,
                  transition: 'all 0.3s ease',
                }}
              >
                {saving ? (
                  <span style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', gap: 8 }}>
                    <span style={{
                      width: 14, height: 14,
                      border: '2px solid rgba(255,255,255,0.3)',
                      borderTopColor: '#fff',
                      borderRadius: '50%',
                      display: 'inline-block',
                      animation: 'spin 0.8s linear infinite',
                    }} />
                    saving...
                  </span>
                ) : step === steps.length - 1 ? 'finish setup →' : 'continue →'}
              </button>
            </div>
          )}

          {/* Skip */}
          <button
            onClick={() => {
              if (step < steps.length - 1) {
                setAnimating(true)
                setTimeout(() => { setStep(s => s + 1); setValue(''); setAnimating(false) }, 250)
              } else {
                localStorage.setItem(onboardingKey, 'true')
                navigate('/dashboard')
              }
            }}
            style={{
              marginTop: 20,
              fontFamily: 'JetBrains Mono, monospace',
              fontSize: 11,
              color: '#2A2A3E',
              background: 'none',
              border: 'none',
              cursor: 'pointer',
              transition: 'color 0.2s',
            }}
            onMouseEnter={e => e.target.style.color = '#4A4A6A'}
            onMouseLeave={e => e.target.style.color = '#2A2A3E'}
          >
            skip for now
          </button>
        </div>

        {/* Step dots */}
        <div style={{ display: 'flex', justifyContent: 'center', gap: 8, marginTop: 28 }}>
          {steps.map((s, i) => (
            <div key={i} style={{
              width: i === step ? 24 : 6,
              height: 6,
              borderRadius: 3,
              background: i === step ? current.accent : i < step ? `${current.accent}50` : '#1A1A2E',
              transition: 'all 0.4s cubic-bezier(0.16,1,0.3,1)',
            }} />
          ))}
        </div>
      </div>

      <style>{`
        @keyframes spin { to { transform: rotate(360deg); } }
      `}</style>
    </div>
  )
}
