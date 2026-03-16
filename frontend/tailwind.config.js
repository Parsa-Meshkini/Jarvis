export default {
  content: ['./index.html', './src/**/*.{js,jsx}'],
  theme: {
    extend: {
      fontFamily: {
        display: ['"DM Serif Display"', 'serif'],
        mono:    ['"JetBrains Mono"', 'monospace'],
        body:    ['"DM Sans"', 'sans-serif'],
      },
      colors: {
        jarvis: {
          bg:      '#0A0A0F',
          surface: '#111118',
          border:  '#1E1E2E',
          dim:     '#2A2A3E',
          accent:  '#6C63FF',
          glow:    '#8B83FF',
          amber:   '#F59E0B',
          green:   '#10B981',
          red:     '#EF4444',
          muted:   '#4A4A6A',
          text:    '#E2E2F0',
          sub:     '#8888AA',
        }
      },
      animation: {
        'fade-in':    'fadeIn 0.4s ease forwards',
        'slide-up':   'slideUp 0.3s ease forwards',
        'glow-pulse': 'glowPulse 2s ease-in-out infinite',
      },
      keyframes: {
        fadeIn:    { from: { opacity: '0' }, to: { opacity: '1' } },
        slideUp:   { from: { opacity: '0', transform: 'translateY(12px)' }, to: { opacity: '1', transform: 'translateY(0)' } },
        glowPulse: { '0%, 100%': { boxShadow: '0 0 8px #6C63FF44' }, '50%': { boxShadow: '0 0 24px #6C63FF88' } },
      },
    },
  },
  plugins: [],
}
