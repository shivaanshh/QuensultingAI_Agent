import { useState, type FormEvent } from 'react'
import { Save } from 'lucide-react'
import { api, ApiError } from '../../api/client'
import type { TenantSettingsUpdate } from '../../api/types'
import { usePortal } from '../../components/layout/PortalShell'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import { Input, Label, Select, Textarea } from '../../components/ui/Field'
import { Button } from '../../components/ui/Button'
import { Alert } from '../../components/ui/Alert'

const WEEKDAYS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export function Settings() {
  const { tenant, reload } = usePortal()
  const [form, setForm] = useState<Required<Omit<TenantSettingsUpdate, 'open_weekdays'>> & { open_weekdays: number[] }>({
    business_name: tenant.business_name,
    timezone: tenant.timezone,
    open_hour: tenant.open_hour,
    close_hour: tenant.close_hour,
    open_weekdays: [...tenant.open_weekdays],
    address: tenant.address,
    transfer_number: tenant.transfer_number,
    notification_email: tenant.notification_email,
    status: tenant.status,
  })
  const [saving, setSaving] = useState(false)
  const [result, setResult] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)

  function set<K extends keyof typeof form>(key: K, value: (typeof form)[K]) {
    setForm((f) => ({ ...f, [key]: value }))
  }

  function toggleDay(d: number) {
    setForm((f) => ({
      ...f,
      open_weekdays: f.open_weekdays.includes(d) ? f.open_weekdays.filter((x) => x !== d) : [...f.open_weekdays, d].sort(),
    }))
  }

  async function save(e: FormEvent) {
    e.preventDefault()
    setResult(null)
    if (form.close_hour <= form.open_hour) {
      setResult({ tone: 'error', text: 'Closing hour must be after opening hour.' })
      return
    }
    if (form.open_weekdays.length === 0) {
      setResult({ tone: 'error', text: 'Select at least one open day.' })
      return
    }
    setSaving(true)
    try {
      await api.updateSettings(tenant.slug, form)
      setResult({ tone: 'success', text: 'Changes saved.' })
      reload()
    } catch (err) {
      setResult({ tone: 'error', text: err instanceof ApiError ? err.message : 'Could not save changes.' })
    } finally {
      setSaving(false)
    }
  }

  return (
    <form onSubmit={save} className="max-w-2xl space-y-6">
      <Card>
        <CardHeader className="text-sm font-semibold">Business information</CardHeader>
        <CardBody className="space-y-4">
          <div>
            <Label htmlFor="bn">Business name</Label>
            <Input id="bn" value={form.business_name} onChange={(e) => set('business_name', e.target.value)} required />
          </div>
          <div>
            <Label htmlFor="addr">Address</Label>
            <Textarea id="addr" rows={2} value={form.address} onChange={(e) => set('address', e.target.value)} />
          </div>
          <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
            <div>
              <Label htmlFor="tn">Transfer number</Label>
              <Input id="tn" value={form.transfer_number} onChange={(e) => set('transfer_number', e.target.value)} placeholder="Where to send escalated calls" />
            </div>
            <div>
              <Label htmlFor="ne">Notification email</Label>
              <Input id="ne" type="email" value={form.notification_email} onChange={(e) => set('notification_email', e.target.value)} />
            </div>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader className="text-sm font-semibold">Working hours</CardHeader>
        <CardBody className="space-y-4">
          <div className="grid grid-cols-3 gap-4">
            <div>
              <Label htmlFor="tz">Timezone</Label>
              <Input id="tz" value={form.timezone} onChange={(e) => set('timezone', e.target.value)} />
            </div>
            <div>
              <Label htmlFor="oh">Opens (0-23)</Label>
              <Input id="oh" type="number" min={0} max={23} value={form.open_hour} onChange={(e) => set('open_hour', Number(e.target.value))} />
            </div>
            <div>
              <Label htmlFor="ch">Closes (0-23)</Label>
              <Input id="ch" type="number" min={0} max={23} value={form.close_hour} onChange={(e) => set('close_hour', Number(e.target.value))} />
            </div>
          </div>
          <div>
            <Label>Open days</Label>
            <div className="flex flex-wrap gap-2">
              {WEEKDAYS.map((label, d) => {
                const on = form.open_weekdays.includes(d)
                return (
                  <button key={d} type="button" onClick={() => toggleDay(d)}
                    className="rounded-lg px-3 py-1.5 text-sm font-medium transition-colors"
                    style={on ? { background: 'rgb(var(--ac-rgb))', color: '#fff' } : { background: 'transparent', color: 'var(--tx-2)', border: '1px solid var(--bd)' }}>
                    {label}
                  </button>
                )
              })}
            </div>
          </div>
        </CardBody>
      </Card>

      <Card>
        <CardHeader className="text-sm font-semibold">Receptionist status</CardHeader>
        <CardBody className="space-y-4">
          <div>
            <Label htmlFor="st">Status</Label>
            <Select id="st" value={form.status} onChange={(e) => set('status', e.target.value)}>
              <option value="active">Active — answering calls</option>
              <option value="paused">Paused — not answering</option>
              <option value="draft">Draft — not yet live</option>
            </Select>
          </div>
          <p className="text-xs" style={{ color: 'var(--tx-3)' }}>
            Pausing keeps all your data but stops the receptionist from being served on public webhooks.
          </p>
        </CardBody>
      </Card>

      {result && <Alert tone={result.tone}>{result.text}</Alert>}

      <div className="flex justify-end">
        <Button type="submit" disabled={saving}>
          <Save size={16} /> {saving ? 'Saving…' : 'Save changes'}
        </Button>
      </div>
    </form>
  )
}
