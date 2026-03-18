import { useNavigate } from 'react-router-dom'

export default function HomePage() {
  const navigate = useNavigate()

  const features = [
    { icon: '🤖', title: 'AI Planning',         desc: 'Gemini understands your request and builds a step-by-step execution plan.' },
    { icon: '📍', title: 'Real location search', desc: 'Finds actual businesses near you using Google Maps in real time.' },
    { icon: '📞', title: 'Voice calling',        desc: 'Calls businesses on your behalf and holds a natural conversation.' },
    { icon: '🗓',  title: 'Calendar aware',       desc: 'Checks your real Google Calendar before booking anything.' },
    { icon: '🧠', title: 'Memory',               desc: 'Remembers your preferences and location between sessions.' },
    { icon: '💾', title: 'Task history',          desc: 'Every task is saved to a database so you can review what Jarvis did.' },
  ]

  return (
    <div className="min-h-screen bg-jarvis-bg text-jarvis-text font-body">

      {/* Nav */}
      <nav className="flex items-center justify-between px-8 py-5 border-b border-jarvis-border">
        <div className="flex items-center gap-3">
        {/* Nav logo */}
        <div className="flex items-center gap-3">
          <img src="resources/android-chrome-192x192.png" alt="Jarvis" className="w-8 h-8 rounded-lg object-cover" />
          <span className="font-display text-jarvis-text text-lg">Jarvis</span>
        </div>
          <span className="font-display text-jarvis-text text-lg">Jarvis</span>
        </div>
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate('/login')}
            className="font-mono text-jarvis-sub text-sm hover:text-jarvis-text transition-colors px-4 py-2"
          >
            sign in
          </button>
          <button
            onClick={() => navigate('/signup')}
            className="bg-jarvis-accent text-white font-mono text-sm px-5 py-2 rounded-lg hover:bg-jarvis-glow transition-colors"
          >
            get started
          </button>
        </div>
      </nav>

      {/* Hero */}
      <section className="flex flex-col items-center justify-center text-center px-6 py-28 gap-6">
        <div className="inline-flex items-center gap-2 border border-jarvis-accent/30 bg-jarvis-accent/5 text-jarvis-accent font-mono text-xs px-4 py-2 rounded-full mb-2">
          {/* Remove the demo window dots and replace logo reference */}
          <img src="/android-chrome-192x192.png" alt="Jarvis" className="w-8 h-8 rounded-lg" />
          <span className="w-2 h-2 bg-jarvis-green rounded-full animate-pulse" />
          autonomous AI assistant
        </div>

        <h1 className="font-display text-5xl sm:text-7xl text-jarvis-text max-w-3xl leading-tight">
          Your personal AI that actually does things
        </h1>

        <p className="text-jarvis-sub text-lg max-w-xl leading-relaxed">
          Jarvis understands what you need, finds the best options, calls businesses on your behalf, and books appointments — all from a single command.
        </p>

        <div className="flex gap-3 mt-4">
          <button
            onClick={() => navigate('/signup')}
            className="bg-jarvis-accent text-white font-mono px-8 py-3 rounded-xl hover:bg-jarvis-glow transition-colors text-sm"
          >
            start for free
          </button>
          <button
            onClick={() => navigate('/login')}
            className="border border-jarvis-border text-jarvis-sub font-mono px-8 py-3 rounded-xl hover:border-jarvis-accent hover:text-jarvis-accent transition-colors text-sm"
          >
            sign in
          </button>
        </div>

        {/* Demo command */}
        <div className="mt-8 border border-jarvis-border bg-jarvis-surface rounded-xl px-6 py-4 max-w-lg w-full text-left">
          <div className="flex items-center gap-2 mb-3">
            <span className="w-2.5 h-2.5 rounded-full bg-jarvis-red" />
            <span className="w-2.5 h-2.5 rounded-full bg-jarvis-amber" />
            <span className="w-2.5 h-2.5 rounded-full bg-jarvis-green" />
          </div>
          <p className="font-mono text-jarvis-accent text-sm">&gt;_ Book me a haircut tomorrow afternoon</p>
          <div className="mt-3 space-y-1.5">
            {[
              { icon: '✓', text: 'Checked your calendar — free at 2pm', color: 'text-jarvis-green' },
              { icon: '✓', text: 'Found Style Studio nearby ⭐ 4.8',      color: 'text-jarvis-green' },
              { icon: '✓', text: 'Called salon and booked 2pm slot',       color: 'text-jarvis-green' },
              { icon: '✓', text: 'Added to Google Calendar',               color: 'text-jarvis-green' },
            ].map((s, i) => (
              <div key={i} className={`flex items-center gap-2 font-mono text-xs ${s.color}`}>
                <span>{s.icon}</span>
                <span>{s.text}</span>
              </div>
            ))}
          </div>
        </div>
      </section>

      {/* Features */}
      <section className="px-8 py-20 max-w-6xl mx-auto">
        <h2 className="font-display text-3xl text-center text-jarvis-text mb-12">
          Everything Jarvis can do
        </h2>
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
          {features.map((f, i) => (
            <div key={i} className="border border-jarvis-border bg-jarvis-surface rounded-xl p-6 hover:border-jarvis-accent/40 transition-colors">
              <div className="text-2xl mb-3">{f.icon}</div>
              <h3 className="font-mono text-jarvis-text text-sm font-medium mb-2">{f.title}</h3>
              <p className="text-jarvis-sub text-xs leading-relaxed">{f.desc}</p>
            </div>
          ))}
        </div>
      </section>

      {/* CTA */}
      <section className="px-8 py-20 text-center border-t border-jarvis-border">
        <h2 className="font-display text-3xl text-jarvis-text mb-4">Ready to try it?</h2>
        <p className="text-jarvis-sub text-sm mb-8">Free to use. No credit card required.</p>
        <button
          onClick={() => navigate('/signup')}
          className="bg-jarvis-accent text-white font-mono px-10 py-3 rounded-xl hover:bg-jarvis-glow transition-colors"
        >
          create your account
        </button>
      </section>

      {/* Footer */}
      <footer className="px-8 py-6 border-t border-jarvis-border text-center">
        <p className="font-mono text-jarvis-muted text-xs">
          Built with FastAPI · Gemini · Google Maps · Twilio · ElevenLabs
        </p>
      </footer>
    </div>
  )
}