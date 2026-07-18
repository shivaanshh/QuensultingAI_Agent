import type { ReactNode } from 'react'

type Tone = 'error' | 'success' | 'info'

const toneStyles: Record<Tone, { bg: string; color: string; border: string }> = {
  error: { bg: 'rgba(239,68,68,.10)', color: 'var(--error)', border: 'rgba(239,68,68,.28)' },
  success: { bg: 'rgba(16,185,129,.10)', color: 'var(--success)', border: 'rgba(16,185,129,.28)' },
  info: { bg: 'rgba(var(--ac-rgb),.10)', color: 'rgb(var(--ac-rgb))', border: 'rgba(var(--ac-rgb),.28)' },
}

export function Alert({ tone = 'info', children }: { tone?: Tone; children: ReactNode }) {
  const s = toneStyles[tone]
  return (
    <div
      className="rounded-xl border px-4 py-3 text-sm"
      style={{ background: s.bg, color: s.color, borderColor: s.border }}
    >
      {children}
    </div>
  )
}
