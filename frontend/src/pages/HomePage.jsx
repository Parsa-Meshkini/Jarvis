import { useNavigate } from 'react-router-dom'
import { useEffect, useRef, useState } from 'react'

function useMousePosition() {
  const [pos, setPos] = useState({ x: 0, y: 0 })
  useEffect(() => {
    const handler = e => setPos({ x: e.clientX, y: e.clientY })
    window.addEventListener('mousemove', handler)
    return () => window.removeEventListener('mousemove', handler)
  }, [])
  return pos
}

const PARTICLES = Array.from({ length: 24 }, (_, i) => ({
  id: i,
  size: Math.random() * 4 + 1.5,
  left: Math.random() * 100,
  top: Math.random() * 100,
  delay: Math.random() * 6,
  duration: Math.random() * 10 + 8,
  opacity: Math.random() * 0.35 + 0.08,
}))

const STEPS = [
  { icon: '🔍', label: 'search_places', text: 'Found Throne Barbershop ⭐ 4.8', color: '#6C63FF' },
  { icon: '🗓', label: 'check_calendar', text: 'Free tomorrow at 2pm', color: '#06B6D4' },
  { icon: '📞', label: 'call_business', text: 'Calling Throne Barbershop...', color: '#F59E0B' },
  { icon: '✓',  label: 'add_to_calendar', text: 'Added to Google Calendar', color: '#10B981' },
]

function AnimatedTerminal() {
  const [active, setActive] = useState(0)
  const [typed, setTyped] = useState('')
  const [showSteps, setShowSteps] = useState(false)
  const [visibleSteps, setVisibleSteps] = useState(0)
  const full = 'Book me a haircut tomorrow afternoon'

  useEffect(() => {
    let t = 0
    const typeInterval = setInterval(() => {
      t++
      setTyped(full.slice(0, t))
      if (t >= full.length) {
        clearInterval(typeInterval)
        setTimeout(() => setShowSteps(true), 400)
      }
    }, 42)
    return () => clearInterval(typeInterval)
  }, [])

  useEffect(() => {
    if (!showSteps) return
    let i = 0
    const reveal = setInterval(() => {
      i++
      setVisibleSteps(i)
      if (i >= STEPS.length) clearInterval(reveal)
    }, 700)
    return () => clearInterval(reveal)
  }, [showSteps])

  return (
    <div style={{
      background: 'rgba(10,10,18,0.95)',
      border: '1px solid rgba(108,99,255,0.25)',
      borderRadius: 16,
      padding: '20px 24px',
      fontFamily: 'JetBrains Mono, monospace',
      boxShadow: '0 0 60px rgba(108,99,255,0.15), 0 30px 80px rgba(0,0,0,0.6)',
      maxWidth: 480,
      width: '100%',
    }}>
      <div style={{ display: 'flex', gap: 6, marginBottom: 16 }}>
        {['#FF5F56','#FFBD2E','#27C93F'].map(c => (
          <div key={c} style={{ width: 10, height: 10, borderRadius: '50%', background: c }} />
        ))}
        <span style={{ marginLeft: 8, color: '#3A3A5A', fontSize: 11 }}>jarvis — terminal</span>
      </div>
      <div style={{ marginBottom: 16 }}>
        <span style={{ color: '#6C63FF', fontSize: 13 }}>❯ </span>
        <span style={{ color: '#E2E2F0', fontSize: 13 }}>{typed}</span>
        <span style={{
          display: 'inline-block', width: 2, height: 14, background: '#6C63FF',
          marginLeft: 2, verticalAlign: 'middle',
          animation: typed.length < full.length ? 'blink 0.7s infinite' : 'none',
        }} />
      </div>
      {showSteps && (
        <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
          {STEPS.slice(0, visibleSteps).map((s, i) => (
            <div key={i} style={{
              display: 'flex', alignItems: 'center', gap: 10,
              animation: 'stepIn 0.4s cubic-bezier(0.16,1,0.3,1) forwards',
              opacity: 0,
              animationFillMode: 'forwards',
            }}>
              <div style={{
                width: 22, height: 22, borderRadius: 6,
                background: `${s.color}20`,
                border: `1px solid ${s.color}50`,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 11, flexShrink: 0,
              }}>{s.icon}</div>
              <span style={{ color: s.color, fontSize: 11, flexShrink: 0 }}>{s.label}</span>
              <span style={{ color: '#5A5A7A', fontSize: 11, marginLeft: 'auto' }}>{s.text}</span>
            </div>
          ))}
          {visibleSteps >= STEPS.length && (
            <div style={{
              marginTop: 6, padding: '8px 12px',
              background: 'rgba(16,185,129,0.08)',
              border: '1px solid rgba(16,185,129,0.2)',
              borderRadius: 8,
              color: '#10B981', fontSize: 11,
              animation: 'stepIn 0.4s 0.1s cubic-bezier(0.16,1,0.3,1) forwards',
              opacity: 0, animationFillMode: 'forwards',
            }}>
              ✓ all done — 4 steps completed in 3.2s
            </div>
          )}
        </div>
      )}
    </div>
  )
}

const features = [
  { icon: '🤖', title: 'AI Planning', desc: 'GPT-4o-mini breaks your request into a precise multi-step execution plan.', color: '#6C63FF' },
  { icon: '📍', title: 'Real Location Search', desc: 'Finds actual businesses near you using Google Maps in real time.', color: '#06B6D4' },
  { icon: '📞', title: 'Voice Calling', desc: 'Calls businesses on your behalf and holds a full two-way conversation.', color: '#F59E0B' },
  { icon: '🗓', title: 'Calendar Aware', desc: 'Checks your real Google Calendar before booking anything.', color: '#10B981' },
  { icon: '🧠', title: 'Memory', desc: 'Learns your preferences — name, location, and ideal booking times.', color: '#EC4899' },
  { icon: '💾', title: 'Full History', desc: 'Every task persisted to a database with step-by-step breakdowns.', color: '#8B5CF6' },
]

export default function HomePage() {
  const navigate = useNavigate()
  const mouse = useMousePosition()
  const heroRef = useRef(null)

  return (
    <div style={{ minHeight: '100vh', background: '#0A0A0F', color: '#E2E2F0', overflowX: 'hidden' }}>
      <style>{`
        @keyframes blink { 0%,100% { opacity:1 } 50% { opacity:0 } }
        @keyframes float { 0%,100% { transform:translateY(0) rotate(0deg) } 50% { transform:translateY(-22px) rotate(180deg) } }
        @keyframes orb { 0%,100% { transform:translate(0,0) scale(1) } 50% { transform:translate(40px,30px) scale(1.08) } }
        @keyframes orb2 { 0%,100% { transform:translate(0,0) scale(1) } 50% { transform:translate(-30px,-20px) scale(1.05) } }
        @keyframes stepIn { from { opacity:0; transform:translateX(-10px) } to { opacity:1; transform:translateX(0) } }
        @keyframes fadeUp { from { opacity:0; transform:translateY(30px) } to { opacity:1; transform:translateY(0) } }
        @keyframes shimmer { 0% { background-position:-200% 0 } 100% { background-position:200% 0 } }
        @keyframes spin { to { transform:rotate(360deg) } }
        @keyframes pulse-slow { 0%,100% { opacity:0.5 } 50% { opacity:1 } }
        .hero-btn-primary:hover { transform:translateY(-2px); box-shadow:0 12px 40px rgba(108,99,255,0.4) !important; }
        .hero-btn-secondary:hover { border-color:rgba(108,99,255,0.6) !important; color:#6C63FF !important; transform:translateY(-2px); }
        .feature-card:hover { border-color:var(--card-accent) !important; transform:translateY(-4px); }
        .feature-card:hover .feature-icon { transform:scale(1.1) rotate(-5deg); }
        .nav-link:hover { color:#E2E2F0 !important; }
        * { transition-timing-function: cubic-bezier(0.16,1,0.3,1); }
      `}</style>

      {/* Navbar */}
      <nav style={{
        display: 'flex', alignItems: 'center', justifyContent: 'space-between',
        padding: '16px 48px',
        borderBottom: '1px solid rgba(108,99,255,0.1)',
        backdropFilter: 'blur(12px)',
        background: 'rgba(10,10,15,0.8)',
        position: 'sticky', top: 0, zIndex: 50,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
          <img src="/jarvis-logo.svg" alt="Jarvis" style={{ width: 32, height: 32, borderRadius: 8, objectFit: 'cover' }} />
          <span style={{ fontFamily: 'Syne, sans-serif', fontSize: 20, fontWeight: 700, color: '#E2E2F0' }}>Jarvis</span>
        </div>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <button className="nav-link" onClick={() => navigate('/login')} style={{
            fontFamily: 'JetBrains Mono, monospace', fontSize: 13, color: '#6A6A8A',
            background: 'none', border: 'none', cursor: 'pointer', padding: '8px 16px',
            transition: 'color 0.2s',
          }}>sign in</button>
          <button onClick={() => navigate('/signup')} style={{
            fontFamily: 'JetBrains Mono, monospace', fontSize: 13,
            background: '#6C63FF', color: '#fff',
            border: 'none', borderRadius: 10, padding: '9px 20px',
            cursor: 'pointer',
            boxShadow: '0 4px 20px rgba(108,99,255,0.3)',
            transition: 'all 0.2s',
          }}
          onMouseEnter={e => { e.target.style.background = '#7C73FF'; e.target.style.transform = 'translateY(-1px)' }}
          onMouseLeave={e => { e.target.style.background = '#6C63FF'; e.target.style.transform = 'translateY(0)' }}
          >get started</button>
        </div>
      </nav>

      {/* Hero */}
      <section ref={heroRef} style={{
        position: 'relative', overflow: 'hidden',
        padding: '100px 24px 120px',
        display: 'flex', flexDirection: 'column', alignItems: 'center',
        textAlign: 'center',
      }}>
        {/* Background orbs */}
        <div style={{ position: 'absolute', inset: 0, overflow: 'hidden', pointerEvents: 'none' }}>
          <div style={{ position:'absolute', width:700, height:700, borderRadius:'50%', background:'radial-gradient(circle, rgba(108,99,255,0.18) 0%, transparent 70%)', top:'-20%', left:'-15%', animation:'orb 14s ease-in-out infinite' }} />
          <div style={{ position:'absolute', width:500, height:500, borderRadius:'50%', background:'radial-gradient(circle, rgba(6,182,212,0.12) 0%, transparent 70%)', bottom:'-10%', right:'-10%', animation:'orb2 18s ease-in-out infinite' }} />
          <div style={{ position:'absolute', width:400, height:400, borderRadius:'50%', background:'radial-gradient(circle, rgba(245,158,11,0.08) 0%, transparent 70%)', top:'30%', right:'20%', animation:'orb 22s ease-in-out infinite reverse' }} />
        </div>

        {/* Particles */}
        {PARTICLES.map(p => (
          <div key={p.id} style={{
            position: 'absolute',
            width: p.size, height: p.size,
            borderRadius: '50%',
            background: p.id % 3 === 0 ? '#6C63FF' : p.id % 3 === 1 ? '#06B6D4' : '#F59E0B',
            left: `${p.left}%`, top: `${p.top}%`,
            opacity: p.opacity,
            animation: `float ${p.duration}s ${p.delay}s ease-in-out infinite`,
            pointerEvents: 'none',
          }} />
        ))}

        {/* Grid */}
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: 'linear-gradient(rgba(108,99,255,0.04) 1px, transparent 1px), linear-gradient(90deg, rgba(108,99,255,0.04) 1px, transparent 1px)',
          backgroundSize: '80px 80px',
          pointerEvents: 'none',
        }} />

        {/* Cursor glow follower */}
        <div style={{
          position: 'fixed',
          width: 300, height: 300,
          borderRadius: '50%',
          background: 'radial-gradient(circle, rgba(108,99,255,0.06) 0%, transparent 70%)',
          left: mouse.x - 150, top: mouse.y - 150,
          pointerEvents: 'none',
          zIndex: 0,
          transition: 'left 0.1s, top 0.1s',
        }} />

        {/* Badge */}
        <div style={{
          display: 'inline-flex', alignItems: 'center', gap: 8,
          border: '1px solid rgba(108,99,255,0.3)',
          background: 'rgba(108,99,255,0.08)',
          borderRadius: 100, padding: '6px 16px',
          fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: '#9B93FF',
          marginBottom: 28, position: 'relative', zIndex: 1,
          animation: 'fadeUp 0.6s 0.1s both',
        }}>
          <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#10B981', animation: 'pulse-slow 2s infinite' }} />
          autonomous AI assistant · powered by gpt-4o-mini
        </div>

        {/* Headline */}
        <h1 style={{
          fontFamily: 'Syne, sans-serif',
          fontSize: 'clamp(42px, 7vw, 80px)',
          fontWeight: 800,
          lineHeight: 1.05,
          maxWidth: 820,
          marginBottom: 24,
          position: 'relative', zIndex: 1,
          animation: 'fadeUp 0.6s 0.2s both',
          letterSpacing: '-0.02em',
        }}>
          Your personal AI that{' '}
          <span style={{
            background: 'linear-gradient(135deg, #6C63FF 0%, #06B6D4 50%, #10B981 100%)',
            WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent',
            backgroundSize: '200% 200%',
            animation: 'shimmer 4s linear infinite',
          }}>
            actually does things
          </span>
        </h1>

        {/* Subheadline */}
        <p style={{
          color: '#6A6A8A', fontSize: 18, maxWidth: 560, lineHeight: 1.7,
          marginBottom: 40, position: 'relative', zIndex: 1,
          animation: 'fadeUp 0.6s 0.3s both',
        }}>
          Jarvis understands your request, finds the best options, calls businesses on your behalf, and books appointments — all from a single command.
        </p>

        {/* CTA buttons */}
        <div style={{
          display: 'flex', gap: 12, marginBottom: 64,
          position: 'relative', zIndex: 1,
          animation: 'fadeUp 0.6s 0.4s both',
        }}>
          <button className="hero-btn-primary" onClick={() => navigate('/signup')} style={{
            background: '#6C63FF', color: '#fff',
            fontFamily: 'JetBrains Mono, monospace', fontSize: 14,
            padding: '14px 32px', borderRadius: 14, border: 'none', cursor: 'pointer',
            boxShadow: '0 4px 20px rgba(108,99,255,0.35)',
            transition: 'all 0.25s',
          }}>start for free →</button>
          <button className="hero-btn-secondary" onClick={() => navigate('/login')} style={{
            background: 'transparent',
            color: '#6A6A8A',
            fontFamily: 'JetBrains Mono, monospace', fontSize: 14,
            padding: '14px 32px', borderRadius: 14,
            border: '1px solid rgba(108,99,255,0.2)', cursor: 'pointer',
            transition: 'all 0.25s',
          }}>sign in</button>
        </div>

        {/* Terminal demo */}
        <div style={{
          position: 'relative', zIndex: 1,
          animation: 'fadeUp 0.6s 0.5s both',
          width: '100%', display: 'flex', justifyContent: 'center',
        }}>
          {/* Glow behind terminal */}
          <div style={{
            position: 'absolute', inset: -40,
            background: 'radial-gradient(ellipse at center, rgba(108,99,255,0.12) 0%, transparent 70%)',
            pointerEvents: 'none',
          }} />
          <AnimatedTerminal />
        </div>
      </section>

      {/* Stats bar */}
      <div style={{
        display: 'flex', justifyContent: 'center', gap: 0,
        borderTop: '1px solid rgba(108,99,255,0.1)',
        borderBottom: '1px solid rgba(108,99,255,0.1)',
        background: 'rgba(108,99,255,0.03)',
        padding: '28px 0',
        flexWrap: 'wrap',
      }}>
        {[
          { num: '4', label: 'AI steps per booking' },
          { num: 'Real', label: 'Google Maps search' },
          { num: 'Live', label: 'voice negotiation' },
          { num: '100%', label: 'calendar integrated' },
        ].map((s, i) => (
          <div key={i} style={{
            textAlign: 'center', padding: '0 48px',
            borderRight: i < 3 ? '1px solid rgba(108,99,255,0.1)' : 'none',
          }}>
            <div style={{ fontFamily: 'Syne, sans-serif', fontSize: 28, fontWeight: 800, color: '#6C63FF' }}>{s.num}</div>
            <div style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#4A4A6A', marginTop: 4 }}>{s.label}</div>
          </div>
        ))}
      </div>

      {/* Features */}
      <section style={{ padding: '100px 48px', maxWidth: 1200, margin: '0 auto' }}>
        <div style={{ textAlign: 'center', marginBottom: 64 }}>
          <div style={{
            display: 'inline-block',
            fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#6C63FF',
            background: 'rgba(108,99,255,0.08)', border: '1px solid rgba(108,99,255,0.2)',
            borderRadius: 100, padding: '4px 14px', marginBottom: 16,
          }}>capabilities</div>
          <h2 style={{ fontFamily: 'Syne, sans-serif', fontSize: 40, fontWeight: 800, color: '#E2E2F0' }}>
            Everything Jarvis can do
          </h2>
        </div>

        <div style={{
          display: 'grid',
          gridTemplateColumns: 'repeat(auto-fit, minmax(320px, 1fr))',
          gap: 20,
        }}>
          {features.map((f, i) => (
            <div key={i} className="feature-card" style={{
              '--card-accent': f.color,
              background: 'rgba(17,17,28,0.7)',
              border: '1px solid rgba(255,255,255,0.06)',
              borderRadius: 20,
              padding: '28px 28px 32px',
              cursor: 'default',
              transition: 'all 0.3s',
              backdropFilter: 'blur(10px)',
            }}>
              <div className="feature-icon" style={{
                width: 48, height: 48,
                background: `${f.color}15`,
                border: `1px solid ${f.color}30`,
                borderRadius: 14,
                display: 'flex', alignItems: 'center', justifyContent: 'center',
                fontSize: 22, marginBottom: 18,
                transition: 'transform 0.3s',
              }}>{f.icon}</div>
              <h3 style={{
                fontFamily: 'Syne, sans-serif', fontSize: 17, fontWeight: 700,
                color: '#E2E2F0', marginBottom: 10,
              }}>{f.title}</h3>
              <p style={{
                fontFamily: 'DM Sans, sans-serif', fontSize: 14, color: '#5A5A7A',
                lineHeight: 1.65,
              }}>{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA section */}
      <section style={{
        margin: '0 48px 80px',
        borderRadius: 28,
        background: 'linear-gradient(135deg, rgba(108,99,255,0.12) 0%, rgba(6,182,212,0.08) 50%, rgba(16,185,129,0.08) 100%)',
        border: '1px solid rgba(108,99,255,0.2)',
        padding: '80px 48px',
        textAlign: 'center',
        position: 'relative', overflow: 'hidden',
      }}>
        <div style={{
          position: 'absolute', inset: 0,
          backgroundImage: 'linear-gradient(rgba(108,99,255,0.05) 1px, transparent 1px), linear-gradient(90deg, rgba(108,99,255,0.05) 1px, transparent 1px)',
          backgroundSize: '40px 40px',
          pointerEvents: 'none',
        }} />
        <div style={{ position: 'relative', zIndex: 1 }}>
          <h2 style={{ fontFamily: 'Syne, sans-serif', fontSize: 44, fontWeight: 800, color: '#E2E2F0', marginBottom: 16 }}>
            Ready to try it?
          </h2>
          <p style={{ color: '#5A5A7A', fontSize: 16, marginBottom: 36, fontFamily: 'DM Sans, sans-serif' }}>
            Free to use. No credit card required.
          </p>
          <button onClick={() => navigate('/signup')} style={{
            background: '#6C63FF', color: '#fff',
            fontFamily: 'JetBrains Mono, monospace', fontSize: 15,
            padding: '16px 40px', borderRadius: 14, border: 'none', cursor: 'pointer',
            boxShadow: '0 8px 30px rgba(108,99,255,0.4)',
            transition: 'all 0.25s',
          }}
          onMouseEnter={e => { e.target.style.transform = 'translateY(-2px)'; e.target.style.boxShadow = '0 14px 40px rgba(108,99,255,0.5)' }}
          onMouseLeave={e => { e.target.style.transform = 'translateY(0)'; e.target.style.boxShadow = '0 8px 30px rgba(108,99,255,0.4)' }}
          >
            create your account →
          </button>
        </div>
      </section>

      {/* Footer */}
      <footer style={{
        borderTop: '1px solid rgba(108,99,255,0.1)',
        padding: '28px 48px',
        display: 'flex', justifyContent: 'space-between', alignItems: 'center',
        flexWrap: 'wrap', gap: 12,
      }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 8 }}>
          <img src="/jarvis-logo.svg" alt="Jarvis" style={{ width: 22, height: 22, borderRadius: 5, objectFit: 'cover' }} />
          <span style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 12, color: '#3A3A5A' }}>Jarvis</span>
        </div>
        <p style={{ fontFamily: 'JetBrains Mono, monospace', fontSize: 11, color: '#2A2A4A' }}>
          FastAPI · OpenAI · Google Maps · Twilio · ElevenLabs
        </p>
      </footer>
    </div>
  )
}
