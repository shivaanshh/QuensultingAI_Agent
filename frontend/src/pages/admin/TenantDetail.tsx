import { useCallback, useEffect, useState } from 'react'
import { Link, useParams } from 'react-router-dom'
import { AlertTriangle, ArrowLeft, CheckCircle2, Code2, ExternalLink, Phone, RefreshCw } from 'lucide-react'
import { api, ApiError } from '../../api/client'
import type { ProvisionResult, TenantDetail as TenantDetailType } from '../../api/types'
import { Button } from '../../components/ui/Button'
import { Card, CardBody, CardHeader } from '../../components/ui/Card'
import { Badge, StatusPill } from '../../components/ui/Badge'
import { Alert } from '../../components/ui/Alert'
import { Spinner } from '../../components/ui/Spinner'

interface FlowNode {
  id: string
  name?: string
  type?: string
  instruction?: { text?: string }
}
interface FlowTool {
  name: string
  url: string
}
interface FlowPreview {
  global_prompt?: string
  tools?: FlowTool[]
  nodes?: FlowNode[]
}

const mutedLabel = { color: 'var(--tx-3)' }
const strongVal = { color: 'var(--tx-1)' }

export function TenantDetail() {
  const { slug = '' } = useParams()
  const [tenant, setTenant] = useState<TenantDetailType | null>(null)
  const [error, setError] = useState<string | null>(null)

  const [preview, setPreview] = useState<FlowPreview | null>(null)
  const [previewError, setPreviewError] = useState<string | null>(null)
  const [showRawJson, setShowRawJson] = useState(false)

  const [provisioning, setProvisioning] = useState(false)
  const [provisionError, setProvisionError] = useState<string | null>(null)
  const [provisionResult, setProvisionResult] = useState<ProvisionResult | null>(null)

  const load = useCallback(() => {
    api
      .getTenant(slug)
      .then(setTenant)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Failed to load tenant'))
  }, [slug])

  useEffect(() => {
    load()
  }, [load])

  useEffect(() => {
    api
      .previewTenant(slug)
      .then((flow) => setPreview(flow as FlowPreview))
      .catch((err) => setPreviewError(err instanceof ApiError ? err.message : 'Failed to build preview'))
  }, [slug])

  async function handleProvision() {
    if (!tenant) return
    if (tenant.retell_agent_id) {
      const confirmed = window.confirm(
        `'${tenant.business_name}' already has an agent (${tenant.retell_agent_id}). ` +
          'Re-provisioning creates a NEW, independent agent and flow — it will not modify the existing one. Continue?'
      )
      if (!confirmed) return
    }
    setProvisioning(true)
    setProvisionError(null)
    try {
      const result = await api.provisionTenant(slug, Boolean(tenant.retell_agent_id))
      setProvisionResult(result)
      load()
    } catch (err) {
      setProvisionError(err instanceof ApiError ? err.message : 'Provisioning failed.')
    } finally {
      setProvisioning(false)
    }
  }

  if (error) return <Alert tone="error">{error}</Alert>
  if (!tenant) {
    return (
      <div className="flex justify-center py-16">
        <Spinner className="text-[color:rgb(var(--ac-rgb))]" />
      </div>
    )
  }

  const urgentNode = preview?.nodes?.find((n) => n.id === 'node_emergency')

  return (
    <div className="space-y-6">
      <div>
        <Link to="/admin" className="mb-3 inline-flex items-center gap-1.5 text-xs font-medium" style={mutedLabel}>
          <ArrowLeft size={13} /> All tenants
        </Link>
        <div className="flex flex-wrap items-start justify-between gap-3">
          <div>
            <div className="flex items-center gap-2">
              <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--tx-1)' }}>
                {tenant.business_name}
              </h1>
              <StatusPill status={tenant.status} />
            </div>
            <p className="mt-1 flex items-center gap-2 text-sm" style={mutedLabel}>
              {tenant.slug} · <Badge tone="slate">{tenant.category.replace('_', ' ')}</Badge>
            </p>
          </div>
          <Button onClick={handleProvision} disabled={provisioning}>
            {provisioning ? (
              'Provisioning…'
            ) : tenant.retell_agent_id ? (
              <><RefreshCw size={16} /> Re-provision</>
            ) : (
              'Provision on Retell'
            )}
          </Button>
        </div>
      </div>

      {provisionError && <Alert tone="error">{provisionError}</Alert>}
      {provisionResult && (
        <Alert tone="success">
          <div className="flex items-start gap-2">
            <CheckCircle2 size={16} className="mt-0.5 shrink-0" />
            <div>
              <p className="font-medium">Provisioned successfully.</p>
              <p className="mt-1 text-xs">
                agent_id: <code>{provisionResult.agent_id}</code>
                <br />
                conversation_flow_id: <code>{provisionResult.conversation_flow_id}</code>
              </p>
              <p className="mt-2 text-xs">
                Attaching a phone number to this agent is still a manual step in the Retell dashboard.
              </p>
            </div>
          </div>
        </Alert>
      )}

      <div className="grid gap-6 lg:grid-cols-3">
        <div className="space-y-6 lg:col-span-2">
          <Card>
            <CardHeader className="text-sm font-semibold">Business info</CardHeader>
            <CardBody>
              <dl className="grid grid-cols-2 gap-4 text-sm">
                {[
                  ['Timezone', tenant.timezone],
                  ['Hours', `${tenant.open_hour}:00 – ${tenant.close_hour}:00`],
                  ['Address', tenant.address || '—'],
                  ['Transfer number', tenant.transfer_number || '—'],
                  ['Booking reference prefix', tenant.booking_reference_prefix],
                  ['Notification email', tenant.notification_email || '—'],
                ].map(([label, value]) => (
                  <div key={label}>
                    <dt style={mutedLabel}>{label}</dt>
                    <dd style={strongVal}>{value}</dd>
                  </div>
                ))}
              </dl>
            </CardBody>
          </Card>

          <Card>
            <CardHeader className="text-sm font-semibold">Services</CardHeader>
            <CardBody>
              {tenant.services.length === 0 ? (
                <p className="text-sm" style={mutedLabel}>No services yet.</p>
              ) : (
                <ul>
                  {tenant.services.map((s, i) => (
                    <li key={s.id} className="flex items-center justify-between py-2 text-sm"
                      style={i > 0 ? { borderTop: '1px solid var(--bd)' } : undefined}>
                      <span style={strongVal}>{s.name}</span>
                      <span style={mutedLabel}>{s.price_display}</span>
                    </li>
                  ))}
                </ul>
              )}
            </CardBody>
          </Card>

          <Card>
            <CardHeader className="text-sm font-semibold">Recent bookings</CardHeader>
            <CardBody>
              {tenant.bookings.length === 0 ? (
                <p className="text-sm" style={mutedLabel}>No bookings yet.</p>
              ) : (
                <div className="overflow-x-auto">
                  <table className="w-full text-left text-sm">
                    <thead className="text-xs uppercase tracking-wide" style={mutedLabel}>
                      <tr style={{ borderBottom: '1px solid var(--bd)' }}>
                        <th className="py-2 pr-3 font-medium">Reference</th>
                        <th className="py-2 pr-3 font-medium">Customer</th>
                        <th className="py-2 pr-3 font-medium">Service</th>
                        <th className="py-2 font-medium">When</th>
                      </tr>
                    </thead>
                    <tbody>
                      {tenant.bookings.map((b) => (
                        <tr key={b.id} style={{ borderBottom: '1px solid var(--bd)' }}>
                          <td className="py-2 pr-3 font-medium" style={strongVal}>{b.booking_reference}</td>
                          <td className="py-2 pr-3" style={{ color: 'var(--tx-2)' }}>{b.customer_name}</td>
                          <td className="py-2 pr-3" style={{ color: 'var(--tx-2)' }}>{b.service_name_snapshot}</td>
                          <td className="py-2" style={{ color: 'var(--tx-2)' }}>{b.confirmed_datetime}</td>
                        </tr>
                      ))}
                    </tbody>
                  </table>
                </div>
              )}
            </CardBody>
          </Card>
        </div>

        <div className="space-y-6">
          <Card>
            <CardHeader className="flex items-center justify-between text-sm font-semibold">
              <span>Agent preview</span>
              {preview && (
                <button type="button" onClick={() => setShowRawJson((v) => !v)}
                  className="flex items-center gap-1 text-xs font-medium hover:underline" style={{ color: 'rgb(var(--ac-rgb))' }}>
                  <Code2 size={12} />
                  {showRawJson ? 'Friendly view' : 'View raw JSON'}
                </button>
              )}
            </CardHeader>
            <CardBody>
              {previewError && <Alert tone="error">{previewError}</Alert>}
              {!preview && !previewError && (
                <div className="flex justify-center py-6">
                  <Spinner className="text-[color:rgb(var(--ac-rgb))]" />
                </div>
              )}
              {preview && !showRawJson && (
                <div className="space-y-4 text-sm">
                  {preview.global_prompt && (
                    <div>
                      <p className="mb-1 font-medium" style={strongVal}>Persona / system prompt</p>
                      <p className="max-h-40 overflow-y-auto whitespace-pre-wrap rounded-lg p-3 text-xs"
                        style={{ background: 'var(--bg-raised)', color: 'var(--tx-2)' }}>
                        {preview.global_prompt}
                      </p>
                    </div>
                  )}
                  {urgentNode?.instruction?.text && (
                    <div>
                      <p className="mb-1 flex items-center gap-1 font-medium" style={strongVal}>
                        <AlertTriangle size={13} style={{ color: 'var(--warning)' }} />
                        Urgent-branch trigger
                      </p>
                      <p className="whitespace-pre-wrap rounded-lg p-3 text-xs"
                        style={{ background: 'rgba(245,158,11,.12)', color: 'var(--warning)', border: '1px solid rgba(245,158,11,.22)' }}>
                        {urgentNode.instruction.text}
                      </p>
                    </div>
                  )}
                  {preview.tools && preview.tools.length > 0 && (
                    <div>
                      <p className="mb-1 font-medium" style={strongVal}>Tool URLs</p>
                      <ul className="space-y-1">
                        {preview.tools.map((t) => (
                          <li key={t.name} className="break-all rounded-lg p-2 text-xs" style={{ background: 'var(--bg-raised)' }}>
                            <span className="font-medium" style={{ color: 'var(--tx-2)' }}>{t.name}</span>
                            <br />
                            <span style={mutedLabel}>{t.url}</span>
                          </li>
                        ))}
                      </ul>
                    </div>
                  )}
                </div>
              )}
              {preview && showRawJson && (
                <pre className="max-h-96 overflow-auto rounded-lg p-3 text-xs"
                  style={{ background: 'var(--code-bg)', color: 'var(--code-tx)' }}>
                  {JSON.stringify(preview, null, 2)}
                </pre>
              )}
            </CardBody>
          </Card>

          {tenant.retell_agent_id && (
            <Card>
              <CardHeader className="text-sm font-semibold">Retell IDs</CardHeader>
              <CardBody className="space-y-2 text-xs" style={{ color: 'var(--tx-2)' }}>
                <div className="flex items-center gap-1">
                  <Phone size={12} /> agent_id: <code>{tenant.retell_agent_id}</code>
                </div>
                <div>conversation_flow_id: <code>{tenant.retell_conversation_flow_id}</code></div>
                <div>voice_id: <code>{tenant.retell_voice_id}</code></div>
                <Link to={`/portal/${tenant.slug}`}
                  className="mt-1 inline-flex items-center gap-1 font-medium hover:underline" style={{ color: 'rgb(var(--ac-rgb))' }}>
                  <ExternalLink size={12} /> Open client dashboard
                </Link>
              </CardBody>
            </Card>
          )}
        </div>
      </div>
    </div>
  )
}
