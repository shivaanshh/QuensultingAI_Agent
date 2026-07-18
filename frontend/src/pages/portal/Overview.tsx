import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import {
  CalendarCheck, Clock, Phone, PhoneCall, PhoneForwarded, Sparkles, TrendingUp,
} from 'lucide-react'
import { api } from '../../api/client'
import type { Analytics } from '../../api/types'
import { usePortal } from '../../components/layout/PortalShell'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import { AreaChart, DonutChart } from '../../components/ui/Charts'
import { Spinner } from '../../components/ui/Spinner'

const SENTIMENT_COLOR: Record<string, string> = {
  Positive: 'var(--success)',
  Neutral: 'var(--tx-3)',
  Negative: 'var(--error)',
  Unknown: 'var(--tx-4)',
}

function fmtDate(iso: string) {
  const d = new Date(iso)
  return Number.isNaN(d.getTime()) ? iso : d.toLocaleDateString(undefined, { month: 'short', day: 'numeric' })
}

export function Overview() {
  const { tenant } = usePortal()
  const [a, setA] = useState<Analytics | null>(null)

  useEffect(() => {
    api.getAnalytics(tenant.slug, 30).then(setA).catch(() => setA(null))
  }, [tenant.slug])

  const provisioned = Boolean(tenant.retell_agent_id)

  const kpis = [
    { icon: Phone, label: 'Calls (30d)', value: a ? a.total_calls : '—', accent: true },
    { icon: PhoneCall, label: 'Answered', value: a ? a.answered_calls : '—' },
    { icon: CalendarCheck, label: 'Bookings (30d)', value: a ? a.total_bookings : '—', accent: true },
    { icon: TrendingUp, label: 'Booking rate', value: a ? `${Math.round(a.booking_conversion * 100)}%` : '—' },
  ]

  return (
    <div className="space-y-6">
      {/* KPI row */}
      <div className="grid grid-cols-2 gap-4 lg:grid-cols-4">
        {kpis.map((k) => (
          <div key={k.label} className="card p-5">
            <span className="flex h-9 w-9 items-center justify-center rounded-lg"
              style={{ background: 'rgba(var(--ac-rgb),.10)', border: '1px solid rgba(var(--ac-rgb),.2)' }}>
              <k.icon size={18} style={{ color: 'rgb(var(--ac-rgb))' }} />
            </span>
            <p className="num mt-3" style={{ fontSize: '1.8rem', fontWeight: 700, letterSpacing: '-0.03em', color: k.accent ? 'rgb(var(--ac-rgb))' : 'var(--tx-1)' }}>
              {k.value}
            </p>
            <p className="text-sm" style={{ color: 'var(--tx-3)' }}>{k.label}</p>
          </div>
        ))}
      </div>

      {!provisioned && (
        <Card>
          <CardBody className="flex flex-wrap items-center gap-3">
            <Sparkles size={18} style={{ color: 'var(--warning)' }} />
            <span className="text-sm" style={{ color: 'var(--tx-2)' }}>
              This receptionist isn’t live yet. Once it’s provisioned and answering calls, your metrics appear here automatically.
            </span>
          </CardBody>
        </Card>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        {/* trend */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="flex items-center justify-between text-sm font-semibold">
              <span>Calls &amp; bookings · last 30 days</span>
              <span className="flex items-center gap-3 text-xs font-normal" style={{ color: 'var(--tx-3)' }}>
                <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full" style={{ background: 'rgb(var(--ac-rgb))' }} /> Calls</span>
                <span className="flex items-center gap-1"><span className="h-2 w-2 rounded-full" style={{ background: 'var(--ac-end)' }} /> Bookings</span>
              </span>
            </CardHeader>
            <CardBody>
              {!a ? (
                <div className="flex justify-center py-12"><Spinner className="text-[color:rgb(var(--ac-rgb))]" /></div>
              ) : (
                <>
                  <AreaChart
                    labels={a.series.map((s) => s.date)}
                    series={[
                      { label: 'Calls', color: 'rgb(var(--ac-rgb))', values: a.series.map((s) => s.calls) },
                      { label: 'Bookings', color: 'var(--ac-end)', values: a.series.map((s) => s.bookings) },
                    ]}
                  />
                  <div className="mt-1 flex justify-between text-xs" style={{ color: 'var(--tx-4)' }}>
                    <span>{a.series.length ? fmtDate(a.series[0].date) : ''}</span>
                    <span>{a.series.length ? fmtDate(a.series[a.series.length - 1].date) : ''}</span>
                  </div>
                </>
              )}
            </CardBody>
          </Card>
        </div>

        {/* sentiment */}
        <Card>
          <CardHeader className="text-sm font-semibold">Caller sentiment</CardHeader>
          <CardBody>
            {!a ? (
              <div className="flex justify-center py-12"><Spinner className="text-[color:rgb(var(--ac-rgb))]" /></div>
            ) : a.total_calls === 0 ? (
              <p className="py-8 text-center text-sm" style={{ color: 'var(--tx-3)' }}>No calls in this window yet.</p>
            ) : (
              <div className="flex flex-col items-center gap-4">
                <DonutChart data={a.sentiment.map((s) => ({ label: s.label, value: s.count, color: SENTIMENT_COLOR[s.label] ?? 'var(--tx-4)' }))} />
                <ul className="w-full space-y-1.5">
                  {a.sentiment.map((s) => (
                    <li key={s.label} className="flex items-center gap-2 text-sm">
                      <span className="h-2.5 w-2.5 rounded-sm" style={{ background: SENTIMENT_COLOR[s.label] ?? 'var(--tx-4)' }} />
                      <span style={{ color: 'var(--tx-2)' }}>{s.label}</span>
                      <span className="num ml-auto" style={{ color: 'var(--tx-1)' }}>{s.count}</span>
                    </li>
                  ))}
                </ul>
              </div>
            )}
          </CardBody>
        </Card>
      </div>

      <div className="grid gap-6 lg:grid-cols-3">
        {/* recent bookings */}
        <div className="lg:col-span-2">
          <Card>
            <CardHeader className="flex items-center justify-between text-sm font-semibold">
              <span>Recent bookings</span>
              <Link to={`/portal/${tenant.slug}/bookings`} className="text-xs font-medium hover:underline" style={{ color: 'rgb(var(--ac-rgb))' }}>
                View all
              </Link>
            </CardHeader>
            <CardBody>
              {tenant.bookings.length === 0 ? (
                <p className="py-8 text-center text-sm" style={{ color: 'var(--tx-3)' }}>No bookings yet.</p>
              ) : (
                <ul>
                  {tenant.bookings.slice(0, 6).map((b, i) => (
                    <li key={b.id} className="flex items-center justify-between gap-3 py-2.5 text-sm"
                      style={i > 0 ? { borderTop: '1px solid var(--bd)' } : undefined}>
                      <div className="min-w-0">
                        <p className="truncate font-medium" style={{ color: 'var(--tx-1)' }}>{b.customer_name}</p>
                        <p className="truncate text-xs" style={{ color: 'var(--tx-3)' }}>{b.service_name_snapshot} · {b.confirmed_datetime}</p>
                      </div>
                      <span className="num shrink-0 text-xs" style={{ color: 'var(--tx-3)' }}>{b.booking_reference}</span>
                    </li>
                  ))}
                </ul>
              )}
            </CardBody>
          </Card>
        </div>

        {/* receptionist + stats */}
        <div className="space-y-6">
          <Card>
            <CardHeader className="text-sm font-semibold">At a glance</CardHeader>
            <CardBody className="space-y-3 text-sm">
              <Row icon={Clock} label="Avg call length" value={a ? `${Math.floor(a.avg_call_seconds / 60)}m ${a.avg_call_seconds % 60}s` : '—'} />
              <Row icon={PhoneCall} label="Talk time (30d)" value={a ? `${a.total_call_minutes} min` : '—'} />
              <Row icon={PhoneForwarded} label="Transfers to" value={tenant.transfer_number || '—'} />
              <Row icon={CalendarCheck} label="Active services" value={String(tenant.services.filter((s) => s.is_active).length)} />
            </CardBody>
          </Card>
        </div>
      </div>
    </div>
  )
}

function Row({ icon: Icon, label, value }: { icon: typeof Clock; label: string; value: string }) {
  return (
    <div className="flex items-center justify-between">
      <span className="flex items-center gap-1.5" style={{ color: 'var(--tx-3)' }}>
        <Icon size={14} /> {label}
      </span>
      <span className="num" style={{ color: 'var(--tx-1)' }}>{value}</span>
    </div>
  )
}
