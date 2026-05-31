export default function Logo({ size = 'md', showText = true }) {
  const sizes = {
    sm: 'w-7 h-7',
    md: 'w-10 h-10',
    lg: 'w-14 h-14',
  }

  return (
    <div className="flex items-center gap-3">
      <img
        src="/jarvis-logo.svg"
        alt="Jarvis"
        className={`${sizes[size]} rounded-xl object-cover`}
      />
      {showText && (
        <span className="font-display text-jarvis-text text-xl">Jarvis</span>
      )}
    </div>
  )
}