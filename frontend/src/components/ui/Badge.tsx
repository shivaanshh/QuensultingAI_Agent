import type { HTMLAttributes } from 'react'
import { cn } from '../../lib/cn'

type Tone = 'slate' | 'teal' | 'amber' | 'red' | 'green'

const toneClasses: Record<Tone, string> = {
  slate: 'badge badge-slate',
  teal: 'badge badge-accent',
  amber: 'badge badge-amber',
  red: 'badge badge-red',
  green: 'badge badge-green',
}

interface BadgeProps extends HTMLAttributes<HTMLSpanElement> {
  tone?: Tone
}

export function Badge({ className, tone = 'slate', ...props }: BadgeProps) {
  return <span className={cn(toneClasses[tone], className)} {...props} />
}

export function StatusPill({ status }: { status: string }) {
  const tone: Tone = status === 'active' ? 'green' : status === 'paused' ? 'amber' : 'slate'
  return (
    <Badge tone={tone} className="capitalize">
      {status}
    </Badge>
  )
}
