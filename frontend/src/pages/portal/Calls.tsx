import { useEffect, useState } from 'react'
import {
  ChevronDown, PhoneIncoming, PhoneMissed, PhoneOutgoing,
} from 'lucide-react'
import { api } from '../../api/client'
import type { CallEvent } from '../../api/types'
import { usePortal } from '../../components/layout/PortalShell'
import { Card, CardBody } from '../../components/ui/Card'
import { Spinner } from '../../components/ui/Spinner'

const SENTIMENT_STYLE: Record<string, { c: string; bg: string }> = {
  Positive: { c: 'var(--success)', bg: 'rgba(16,185,129,.12)' },
  Neutral: { c: 'var(--tx-2)', bg: 'var(--bg-raised)' },
  Negative: { c: 'var(--error)', bg: 'rgba(239,68,68,.12)' },
}

function fmtDuration(s: number | null) {
  if (!s) return '—'
  const m = Math.floor(s / 60)
  return `${m}m ${s % 60}s`
}

function fmtWhen(iso: string | null) {
  if (!iso) return '—'
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleString(undefined, { month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit' })
}

export function Calls() {
  const { tenant } = usePortal()
  const [calls, setCalls] = useState<CallEvent[] | null>(null)
  const [open, setOpen] = useState<number | null>(null)

  useEffect(() => {
    api.listCalls(tenant.slug, 100).then(setCalls).catch(() => setCalls([]))
  }, [tenant.slug])

  if (!calls) {
    return <div className="flex justify-center py-16"><Spinner className="text-[color:rgb(var(--ac-rgb))]" /></div>
  }

  if (calls.length === 0) {
    return (
      <Card>
        <CardBody className="px-6 py-16 text-center">
          <PhoneIncoming className="mx-auto mb-3 h-9 w-9" style={{ color: 'var(--tx-4)' }} />
          <p className="font-medium" style={{ color: 'var(--tx-1)' }}>No calls logged yet</p>
          <p className="mx-auto mt-1 max-w-md text-sm" style={{ color: 'var(--tx-3)' }}>
            Calls appear here once your agent’s webhook is connected in Retell and it starts answering.
            Each call shows its duration, outcome, sentiment, and full transcript.
          </p>
        </CardBody>
      </Card>
    )
  }

  return (
    <div className="space-y-3">
      {calls.map((c) => {
        const isOpen = open === c.id
        const missed = c.call_status === 'ongoing' && !c.ended_at
        const Icon = missed ? PhoneMissed : c.direction === 'outbound' ? PhoneOutgoing : PhoneIncoming
        const sent = SENTIMENT_STYLE[c.user_sentiment]
        return (
          <Card key={c.id}>
            <button onClick={() => setOpen(isOpen ? null : c.id)} className="flex w-full items-center gap-4 px-5 py-4 text-left">
              <span className="flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
                style={{ background: 'rgba(var(--ac-rgb),.10)', border: '1px solid rgba(var(--ac-rgb),.2)' }}>
                <Icon size={18} style={{ color: 'rgb(var(--ac-rgb))' }} />
              </span>
              <div className="min-w-0 flex-1">
                <div className="flex flex-wrap items-center gap-2">
                  <span className="num font-medium" style={{ color: 'var(--tx-1)' }}>{c.from_number || 'Unknown caller'}</span>
                  {c.call_successful != null && (
                    <span className="badge" style={c.call_successful
                      ? { color: 'var(--success)', background: 'rgba(16,185,129,.12)', border: '1px solid rgba(16,185,129,.25)' }
                      : { color: 'var(--warning)', background: 'rgba(245,158,11,.14)', border: '1px solid rgba(245,158,11,.28)' }}>
                      {c.call_successful ? 'Successful' : 'Incomplete'}
                    </span>
                  )}
                  {sent && <span className="badge" style={{ color: sent.c, background: sent.bg }}>{c.user_sentiment}</span>}
                </div>
                <p className="truncate text-xs" style={{ color: 'var(--tx-3)' }}>
                  {fmtWhen(c.started_at ?? c.created_at)} · {fmtDuration(c.duration_seconds)}
                  {c.summary ? ` · ${c.summary}` : ''}
                </p>
              </div>
              <ChevronDown size={16} className="shrink-0 transition-transform" style={{ color: 'var(--tx-3)', transform: isOpen ? 'rotate(180deg)' : 'none' }} />
            </button>
            {isOpen && (
              <div className="border-t px-5 py-4 text-sm" style={{ borderColor: 'var(--bd)' }}>
                <div className="mb-3 grid grid-cols-2 gap-3 sm:grid-cols-4">
                  <Meta label="Duration" value={fmtDuration(c.duration_seconds)} />
                  <Meta label="Status" value={c.call_status} />
                  <Meta label="Ended reason" value={c.disconnection_reason || '—'} />
                  <Meta label="To" value={c.to_number || '—'} />
                </div>
                {c.summary && (
                  <div className="mb-3">
                    <p className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--tx-3)' }}>Summary</p>
                    <p style={{ color: 'var(--tx-2)' }}>{c.summary}</p>
                  </div>
                )}
                {c.transcript ? (
                  <div>
                    <p className="mb-1 text-xs font-semibold uppercase tracking-wide" style={{ color: 'var(--tx-3)' }}>Transcript</p>
                    <pre className="max-h-64 overflow-auto whitespace-pre-wrap rounded-lg p-3 text-xs" style={{ background: 'var(--bg-raised)', color: 'var(--tx-2)', fontFamily: 'inherit' }}>
                      {c.transcript}
                    </pre>
                  </div>
                ) : (
                  <p className="text-xs" style={{ color: 'var(--tx-4)' }}>No transcript captured for this call.</p>
                )}
              </div>
            )}
          </Card>
        )
      })}
    </div>
  )
}

function Meta({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-xs" style={{ color: 'var(--tx-3)' }}>{label}</p>
      <p className="num capitalize" style={{ color: 'var(--tx-1)' }}>{value}</p>
    </div>
  )
}
