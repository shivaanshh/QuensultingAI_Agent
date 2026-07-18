import { useMemo, useState } from 'react'
import { CalendarCheck, Check, Search, X } from 'lucide-react'
import { api, ApiError } from '../../api/client'
import type { Booking, BookingStatus } from '../../api/types'
import { usePortal } from '../../components/layout/PortalShell'
import { Card } from '../../components/ui/Card'
import { Input, Select } from '../../components/ui/Field'
import { Alert } from '../../components/ui/Alert'

const STATUSES: { value: BookingStatus; label: string; color: string; bg: string }[] = [
  { value: 'confirmed', label: 'Confirmed', color: 'rgb(var(--ac-rgb))', bg: 'rgba(var(--ac-rgb),.12)' },
  { value: 'completed', label: 'Completed', color: 'var(--success)', bg: 'rgba(16,185,129,.12)' },
  { value: 'cancelled', label: 'Cancelled', color: 'var(--error)', bg: 'rgba(239,68,68,.12)' },
  { value: 'no_show', label: 'No-show', color: 'var(--warning)', bg: 'rgba(245,158,11,.14)' },
]

function statusStyle(status: string) {
  const s = STATUSES.find((x) => x.value === status)
  return s ? { color: s.color, background: s.bg, border: `1px solid ${s.color}33` } : { color: 'var(--tx-3)', background: 'var(--bg-raised)' }
}

export function Bookings() {
  const { tenant, reload } = usePortal()
  const [rows, setRows] = useState<Booking[]>(tenant.bookings)
  const [query, setQuery] = useState('')
  const [filter, setFilter] = useState<string>('all')
  const [busyId, setBusyId] = useState<number | null>(null)
  const [error, setError] = useState<string | null>(null)

  const filtered = useMemo(() => {
    const q = query.trim().toLowerCase()
    return rows.filter((b) => {
      if (filter !== 'all' && b.status !== filter) return false
      if (!q) return true
      return (
        b.customer_name.toLowerCase().includes(q) ||
        b.booking_reference.toLowerCase().includes(q) ||
        b.service_name_snapshot.toLowerCase().includes(q) ||
        (b.phone_number || '').includes(q)
      )
    })
  }, [rows, query, filter])

  async function setStatus(b: Booking, status: BookingStatus) {
    setBusyId(b.id)
    setError(null)
    try {
      const updated = await api.updateBookingStatus(tenant.slug, b.id, status)
      setRows((prev) => prev.map((x) => (x.id === b.id ? { ...x, status: updated.status } : x)))
      reload()
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not update booking.')
    } finally {
      setBusyId(null)
    }
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-center gap-3">
        <div className="relative min-w-[220px] flex-1">
          <Search className="pointer-events-none absolute left-3 top-1/2 h-4 w-4 -translate-y-1/2" style={{ color: 'var(--tx-3)' }} />
          <Input value={query} onChange={(e) => setQuery(e.target.value)} placeholder="Search name, reference, service, phone…" className="pl-9" />
        </div>
        <Select value={filter} onChange={(e) => setFilter(e.target.value)} className="w-auto">
          <option value="all">All statuses</option>
          {STATUSES.map((s) => (
            <option key={s.value} value={s.value}>{s.label}</option>
          ))}
        </Select>
      </div>

      {error && <Alert tone="error">{error}</Alert>}

      <Card className="overflow-hidden">
        {filtered.length === 0 ? (
          <div className="px-6 py-16 text-center">
            <CalendarCheck className="mx-auto mb-2 h-8 w-8" style={{ color: 'var(--tx-4)' }} />
            <p className="text-sm" style={{ color: 'var(--tx-3)' }}>
              {rows.length === 0 ? 'No bookings yet. They appear here as your receptionist takes calls.' : 'No bookings match your filters.'}
            </p>
          </div>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide" style={{ background: 'var(--bg-raised)', color: 'var(--tx-3)', borderBottom: '1px solid var(--bd)' }}>
                <tr>
                  <th className="px-5 py-3 font-medium">Customer</th>
                  <th className="px-5 py-3 font-medium">Service</th>
                  <th className="px-5 py-3 font-medium">When</th>
                  <th className="px-5 py-3 font-medium">Reference</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium text-right">Actions</th>
                </tr>
              </thead>
              <tbody>
                {filtered.map((b) => (
                  <tr key={b.id} style={{ borderBottom: '1px solid var(--bd)' }}>
                    <td className="px-5 py-3">
                      <p className="font-medium" style={{ color: 'var(--tx-1)' }}>{b.customer_name}</p>
                      <p className="num text-xs" style={{ color: 'var(--tx-3)' }}>{b.phone_number}</p>
                    </td>
                    <td className="px-5 py-3" style={{ color: 'var(--tx-2)' }}>{b.service_name_snapshot}</td>
                    <td className="px-5 py-3" style={{ color: 'var(--tx-2)' }}>{b.confirmed_datetime}</td>
                    <td className="px-5 py-3 num text-xs" style={{ color: 'var(--tx-3)' }}>{b.booking_reference}</td>
                    <td className="px-5 py-3">
                      <span className="badge" style={statusStyle(b.status)}>{STATUSES.find((s) => s.value === b.status)?.label ?? b.status}</span>
                    </td>
                    <td className="px-5 py-3">
                      <div className="flex items-center justify-end gap-1.5">
                        {b.status !== 'completed' && (
                          <button onClick={() => setStatus(b, 'completed')} disabled={busyId === b.id}
                            title="Mark completed" className="flex h-7 w-7 items-center justify-center rounded-lg transition-colors disabled:opacity-40"
                            style={{ color: 'var(--success)', background: 'rgba(16,185,129,.1)', border: '1px solid rgba(16,185,129,.25)' }}>
                            <Check size={14} />
                          </button>
                        )}
                        {b.status !== 'cancelled' && (
                          <button onClick={() => setStatus(b, 'cancelled')} disabled={busyId === b.id}
                            title="Cancel booking" className="flex h-7 w-7 items-center justify-center rounded-lg transition-colors disabled:opacity-40"
                            style={{ color: 'var(--error)', background: 'rgba(239,68,68,.08)', border: '1px solid rgba(239,68,68,.22)' }}>
                            <X size={14} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </Card>
      <p className="text-xs" style={{ color: 'var(--tx-4)' }}>Showing the {rows.length} most recent bookings.</p>
    </div>
  )
}
