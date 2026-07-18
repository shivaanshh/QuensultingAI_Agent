import { useEffect, useState } from 'react'
import { Link } from 'react-router-dom'
import { Plus } from 'lucide-react'
import { api, ApiError } from '../../api/client'
import type { TenantListItem } from '../../api/types'
import { buttonClasses } from '../../components/ui/Button'
import { Badge, StatusPill } from '../../components/ui/Badge'
import { Card } from '../../components/ui/Card'
import { Alert } from '../../components/ui/Alert'
import { Spinner } from '../../components/ui/Spinner'

export function TenantsList() {
  const [tenants, setTenants] = useState<TenantListItem[] | null>(null)
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    api
      .listTenants()
      .then(setTenants)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Failed to load tenants'))
  }, [])

  return (
    <div>
      <div className="mb-6 flex items-center justify-between">
        <div>
          <h1 style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--tx-1)' }}>Tenants</h1>
          <p className="text-sm" style={{ color: 'var(--tx-3)' }}>Every business provisioned on the platform.</p>
        </div>
        <Link to="/admin/new" className={buttonClasses({ size: 'md' })}>
          <Plus size={16} />
          New tenant
        </Link>
      </div>

      {error && <Alert tone="error">{error}</Alert>}

      {!tenants && !error && (
        <div className="flex justify-center py-16">
          <Spinner className="text-[color:rgb(var(--ac-rgb))]" />
        </div>
      )}

      {tenants && tenants.length === 0 && (
        <Card>
          <div className="px-6 py-12 text-center text-sm" style={{ color: 'var(--tx-3)' }}>
            No tenants yet. Create the first one to get started.
          </div>
        </Card>
      )}

      {tenants && tenants.length > 0 && (
        <Card className="overflow-hidden">
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead className="text-xs uppercase tracking-wide"
                style={{ background: 'var(--bg-raised)', color: 'var(--tx-3)', borderBottom: '1px solid var(--bd)' }}>
                <tr>
                  <th className="px-5 py-3 font-medium">Business</th>
                  <th className="px-5 py-3 font-medium">Category</th>
                  <th className="px-5 py-3 font-medium">Status</th>
                  <th className="px-5 py-3 font-medium">Provisioned</th>
                  <th className="px-5 py-3 font-medium">Created</th>
                </tr>
              </thead>
              <tbody>
                {tenants.map((t) => (
                  <tr key={t.id} className="transition-colors hover:bg-[var(--bg-raised)]" style={{ borderBottom: '1px solid var(--bd)' }}>
                    <td className="px-5 py-3">
                      <Link to={`/admin/tenants/${t.slug}`} className="font-medium hover:underline" style={{ color: 'rgb(var(--ac-rgb))' }}>
                        {t.business_name}
                      </Link>
                      <div className="text-xs" style={{ color: 'var(--tx-4)' }}>{t.slug}</div>
                    </td>
                    <td className="px-5 py-3">
                      <Badge tone="slate">{t.category.replace('_', ' ')}</Badge>
                    </td>
                    <td className="px-5 py-3">
                      <StatusPill status={t.status} />
                    </td>
                    <td className="px-5 py-3">
                      {t.provisioned ? <Badge tone="teal">Provisioned</Badge> : <Badge tone="amber">Not provisioned</Badge>}
                    </td>
                    <td className="px-5 py-3" style={{ color: 'var(--tx-3)' }}>
                      {new Date(t.created_at).toLocaleDateString()}
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </Card>
      )}
    </div>
  )
}
