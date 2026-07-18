import { useEffect, useState, type FormEvent } from 'react'
import { Plus, Trash2 } from 'lucide-react'
import { api, ApiError } from '../../api/client'
import type { Service } from '../../api/types'
import { usePortal } from '../../components/layout/PortalShell'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import { Input, Label } from '../../components/ui/Field'
import { Button } from '../../components/ui/Button'
import { Alert } from '../../components/ui/Alert'
import { Spinner } from '../../components/ui/Spinner'

export function Services() {
  const { tenant } = usePortal()
  const [services, setServices] = useState<Service[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [name, setName] = useState('')
  const [price, setPrice] = useState('')
  const [duration, setDuration] = useState('')
  const [adding, setAdding] = useState(false)

  useEffect(() => {
    api.listServices(tenant.slug).then(setServices).catch(() => setServices([]))
  }, [tenant.slug])

  async function addService(e: FormEvent) {
    e.preventDefault()
    if (!name.trim()) return
    setAdding(true)
    setError(null)
    try {
      const created = await api.addService(tenant.slug, {
        name: name.trim(),
        price_display: price.trim(),
        duration_minutes: duration ? Number(duration) : null,
      })
      setServices((prev) => [...(prev ?? []), created])
      setName('')
      setPrice('')
      setDuration('')
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not add service.')
    } finally {
      setAdding(false)
    }
  }

  async function toggle(s: Service) {
    try {
      const updated = await api.updateService(tenant.slug, s.id, { is_active: !s.is_active })
      setServices((prev) => (prev ?? []).map((x) => (x.id === s.id ? updated : x)))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not update service.')
    }
  }

  async function remove(s: Service) {
    if (!window.confirm(`Remove “${s.name}”? The receptionist will stop offering it.`)) return
    try {
      await api.deleteService(tenant.slug, s.id)
      setServices((prev) => (prev ?? []).filter((x) => x.id !== s.id))
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Could not remove service.')
    }
  }

  return (
    <div className="grid gap-6 lg:grid-cols-3">
      <div className="lg:col-span-2">
        <Card>
          <CardHeader className="text-sm font-semibold">Services your receptionist offers</CardHeader>
          <CardBody>
            {!services ? (
              <div className="flex justify-center py-10"><Spinner className="text-[color:rgb(var(--ac-rgb))]" /></div>
            ) : services.length === 0 ? (
              <p className="py-8 text-center text-sm" style={{ color: 'var(--tx-3)' }}>No services yet. Add your first one on the right.</p>
            ) : (
              <ul>
                {services.map((s, i) => (
                  <li key={s.id} className="flex items-center gap-3 py-3" style={i > 0 ? { borderTop: '1px solid var(--bd)' } : undefined}>
                    <div className="min-w-0 flex-1">
                      <p className="font-medium" style={{ color: s.is_active ? 'var(--tx-1)' : 'var(--tx-4)' }}>{s.name}</p>
                      <p className="text-xs" style={{ color: 'var(--tx-3)' }}>
                        {s.price_display || 'No price set'}{s.duration_minutes ? ` · ${s.duration_minutes} min` : ''}
                      </p>
                    </div>
                    <label className="flex cursor-pointer items-center gap-2 text-xs" style={{ color: 'var(--tx-3)' }}>
                      <span>{s.is_active ? 'Active' : 'Hidden'}</span>
                      <span onClick={() => toggle(s)}
                        className="relative inline-block h-5 w-9 rounded-full transition-colors"
                        style={{ background: s.is_active ? 'rgb(var(--ac-rgb))' : 'var(--bd-s)' }}>
                        <span className="absolute top-0.5 h-4 w-4 rounded-full bg-white transition-all" style={{ left: s.is_active ? '18px' : '2px' }} />
                      </span>
                    </label>
                    <button onClick={() => remove(s)} title="Remove" className="flex h-8 w-8 items-center justify-center rounded-lg transition-colors"
                      style={{ color: 'var(--tx-3)' }}>
                      <Trash2 size={15} />
                    </button>
                  </li>
                ))}
              </ul>
            )}
          </CardBody>
        </Card>
      </div>

      <div>
        <Card>
          <CardHeader className="text-sm font-semibold">Add a service</CardHeader>
          <CardBody>
            <form onSubmit={addService} className="space-y-4">
              <div>
                <Label htmlFor="svc-name">Name</Label>
                <Input id="svc-name" value={name} onChange={(e) => setName(e.target.value)} placeholder="e.g. Teeth Whitening" required />
              </div>
              <div>
                <Label htmlFor="svc-price">Price (spoken text)</Label>
                <Input id="svc-price" value={price} onChange={(e) => setPrice(e.target.value)} placeholder="e.g. $120 or Starts at ₹500" />
              </div>
              <div>
                <Label htmlFor="svc-dur">Duration (minutes)</Label>
                <Input id="svc-dur" type="number" min={0} max={1440} value={duration} onChange={(e) => setDuration(e.target.value)} placeholder="Optional" />
              </div>
              {error && <Alert tone="error">{error}</Alert>}
              <Button type="submit" disabled={adding} className="w-full">
                <Plus size={16} /> {adding ? 'Adding…' : 'Add service'}
              </Button>
            </form>
          </CardBody>
        </Card>
      </div>
    </div>
  )
}
