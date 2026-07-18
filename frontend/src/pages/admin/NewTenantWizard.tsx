import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { Plus, X } from 'lucide-react'
import { api, ApiError } from '../../api/client'
import type { Category } from '../../api/types'
import { Button } from '../../components/ui/Button'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import { FieldHint, Input, Label, Select } from '../../components/ui/Field'
import { Alert } from '../../components/ui/Alert'

const SLUG_RE = /^[a-z0-9]+(-[a-z0-9]+)*$/
const WEEKDAY_LABELS = ['Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat', 'Sun']

export function NewTenantWizard() {
  const navigate = useNavigate()
  const [categories, setCategories] = useState<Category[]>([])

  const [slug, setSlug] = useState('')
  const [category, setCategory] = useState('')
  const [businessName, setBusinessName] = useState('')
  const [timezone, setTimezone] = useState('Asia/Kolkata')
  const [openHour, setOpenHour] = useState(9)
  const [closeHour, setCloseHour] = useState(18)
  const [openWeekdays, setOpenWeekdays] = useState<number[]>([0, 1, 2, 3, 4, 5])
  const [address, setAddress] = useState('')
  const [transferNumber, setTransferNumber] = useState('')
  const [notificationEmail, setNotificationEmail] = useState('')
  const [services, setServices] = useState<string[]>([])
  const [newService, setNewService] = useState('')

  const [submitting, setSubmitting] = useState(false)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api.getCategories().then(setCategories).catch(() => setCategories([]))
  }, [])

  const selectedCategory = useMemo(
    () => categories.find((c) => c.key === category) ?? null,
    [categories, category]
  )

  function toggleWeekday(day: number) {
    setOpenWeekdays((prev) =>
      prev.includes(day) ? prev.filter((d) => d !== day) : [...prev, day].sort()
    )
  }

  function addService() {
    const name = newService.trim()
    if (!name) return
    setServices((prev) => [...prev, name])
    setNewService('')
  }

  function useSuggestedServices() {
    if (!selectedCategory) return
    setServices(selectedCategory.default_services.map((s) => s.name))
  }

  function validate(): string | null {
    if (!slug || !SLUG_RE.test(slug)) {
      return "Slug must be lowercase letters, digits, and hyphens only (e.g. 'glow-salon')."
    }
    if (!category) return 'Please choose a category.'
    if (!businessName.trim()) return 'Business name is required.'
    if (closeHour <= openHour) return 'Closing hour must be after opening hour.'
    if (openWeekdays.length === 0) return 'Select at least one open day.'
    return null
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const validationError = validate()
    if (validationError) {
      setError(validationError)
      return
    }
    setError(null)
    setSubmitting(true)
    try {
      const tenant = await api.createTenant({
        slug,
        category,
        business_name: businessName,
        timezone,
        open_hour: openHour,
        close_hour: closeHour,
        open_weekdays: openWeekdays,
        address,
        transfer_number: transferNumber,
        notification_email: notificationEmail,
        services,
      })
      navigate(`/admin/tenants/${tenant.slug}`)
    } catch (err) {
      setError(err instanceof ApiError ? err.message : 'Failed to create tenant.')
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="mx-auto max-w-2xl">
      <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--tx-1)' }}>New tenant</h1>
      <p className="mt-1 text-sm" style={{ color: 'var(--tx-3)' }}>
        Creates the tenant record. Provisioning the Retell agent is a separate step from the
        tenant’s detail page.
      </p>

      <form onSubmit={handleSubmit} className="mt-6 space-y-6">
        <Card>
          <CardHeader className="text-sm font-semibold">Business profile</CardHeader>
          <CardBody className="space-y-4">
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor="slug">Slug</Label>
                <Input id="slug" required placeholder="glow-salon" value={slug} onChange={(e) => setSlug(e.target.value)} />
                <FieldHint>Lowercase letters, digits, hyphens. Used in the webhook URL.</FieldHint>
              </div>
              <div>
                <Label htmlFor="category">Category</Label>
                <Select id="category" required value={category} onChange={(e) => setCategory(e.target.value)}>
                  <option value="">Select a category</option>
                  {categories.map((c) => (
                    <option key={c.key} value={c.key}>{c.display_name}</option>
                  ))}
                </Select>
              </div>
            </div>

            <div>
              <Label htmlFor="business_name">Business name</Label>
              <Input id="business_name" required value={businessName} onChange={(e) => setBusinessName(e.target.value)} />
            </div>

            <div>
              <Label htmlFor="address">Address</Label>
              <Input id="address" value={address} onChange={(e) => setAddress(e.target.value)} />
            </div>

            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              <div>
                <Label htmlFor="transfer_number">Transfer number</Label>
                <Input id="transfer_number" placeholder="For calls escalated to a human" value={transferNumber} onChange={(e) => setTransferNumber(e.target.value)} />
              </div>
              <div>
                <Label htmlFor="notification_email">Notification email</Label>
                <Input id="notification_email" type="email" value={notificationEmail} onChange={(e) => setNotificationEmail(e.target.value)} />
              </div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader className="text-sm font-semibold">Hours</CardHeader>
          <CardBody className="space-y-4">
            <div className="grid grid-cols-3 gap-4">
              <div>
                <Label htmlFor="timezone">Timezone</Label>
                <Input id="timezone" value={timezone} onChange={(e) => setTimezone(e.target.value)} />
              </div>
              <div>
                <Label htmlFor="open_hour">Opens (0-23)</Label>
                <Input id="open_hour" type="number" min={0} max={23} value={openHour} onChange={(e) => setOpenHour(Number(e.target.value))} />
              </div>
              <div>
                <Label htmlFor="close_hour">Closes (0-23)</Label>
                <Input id="close_hour" type="number" min={0} max={23} value={closeHour} onChange={(e) => setCloseHour(Number(e.target.value))} />
              </div>
            </div>

            <div>
              <Label>Open days</Label>
              <div className="flex flex-wrap gap-2">
                {WEEKDAY_LABELS.map((label, day) => {
                  const on = openWeekdays.includes(day)
                  return (
                    <button
                      key={day}
                      type="button"
                      onClick={() => toggleWeekday(day)}
                      className="rounded-lg px-3 py-1.5 text-sm font-medium transition-colors"
                      style={on
                        ? { background: 'rgb(var(--ac-rgb))', color: '#fff' }
                        : { background: 'transparent', color: 'var(--tx-2)', border: '1px solid var(--bd)' }}
                    >
                      {label}
                    </button>
                  )
                })}
              </div>
            </div>
          </CardBody>
        </Card>

        <Card>
          <CardHeader className="flex items-center justify-between text-sm font-semibold">
            <span>Starter services</span>
            {selectedCategory && selectedCategory.default_services.length > 0 && (
              <button type="button" onClick={useSuggestedServices}
                className="text-xs font-medium hover:underline" style={{ color: 'rgb(var(--ac-rgb))' }}>
                Use {selectedCategory.display_name} defaults
              </button>
            )}
          </CardHeader>
          <CardBody className="space-y-3">
            {services.length > 0 && (
              <ul className="space-y-2">
                {services.map((s, i) => (
                  <li key={`${s}-${i}`} className="flex items-center justify-between rounded-lg px-3 py-1.5 text-sm"
                    style={{ border: '1px solid var(--bd)', color: 'var(--tx-1)' }}>
                    {s}
                    <button type="button" onClick={() => setServices((prev) => prev.filter((_, idx) => idx !== i))}
                      className="transition-colors" style={{ color: 'var(--tx-3)' }}>
                      <X size={14} />
                    </button>
                  </li>
                ))}
              </ul>
            )}
            <div className="flex gap-2">
              <Input
                placeholder="Add a service"
                value={newService}
                onChange={(e) => setNewService(e.target.value)}
                onKeyDown={(e) => {
                  if (e.key === 'Enter') {
                    e.preventDefault()
                    addService()
                  }
                }}
              />
              <Button type="button" variant="secondary" onClick={addService}>
                <Plus size={16} />
                Add
              </Button>
            </div>
          </CardBody>
        </Card>

        {error && <Alert tone="error">{error}</Alert>}

        <div className="flex justify-end gap-3">
          <Button type="submit" disabled={submitting}>
            {submitting ? 'Creating…' : 'Create tenant'}
          </Button>
        </div>
      </form>
    </div>
  )
}
