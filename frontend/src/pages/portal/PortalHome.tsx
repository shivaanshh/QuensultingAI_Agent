import { useEffect, useMemo, useState, type FormEvent } from 'react'
import { useNavigate } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, Building2, PhoneCall, Search } from 'lucide-react'
import { api, ApiError } from '../../api/client'
import type { TenantListItem } from '../../api/types'
import { Badge, StatusPill } from '../../components/ui/Badge'
import { Input } from '../../components/ui/Field'
import { Alert } from '../../components/ui/Alert'
import { Spinner } from '../../components/ui/Spinner'

export function PortalHome() {
  const navigate = useNavigate()
  const [tenants, setTenants] = useState<TenantListItem[] | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [query, setQuery] = useState('')

  useEffect(() => {
    api
      .listTenants()
      .then(setTenants)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Failed to load businesses'))
  }, [])

  const filtered = useMemo(() => {
    if (!tenants) return []
    const q = query.trim().toLowerCase()
    if (!q) return tenants
    return tenants.filter(
      (t) => t.business_name.toLowerCase().includes(q) || t.slug.toLowerCase().includes(q)
    )
  }, [tenants, query])

  function handleSubmit(e: FormEvent) {
    e.preventDefault()
    const q = query.trim().toLowerCase()
    if (!q) return
    const exact = tenants?.find((t) => t.slug === q)
    if (exact) navigate(`/portal/${exact.slug}`)
    else if (filtered.length === 1) navigate(`/portal/${filtered[0].slug}`)
  }

  return (
    <div className="mx-auto max-w-3xl">
      <motion.div initial={{ opacity: 0, y: 20 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.5 }} className="text-center">
        <span className="mx-auto mb-5 flex h-14 w-14 items-center justify-center rounded-2xl text-white"
          style={{ background: 'linear-gradient(135deg, rgb(var(--ac-rgb)), var(--ac-end))', boxShadow: '0 10px 30px rgba(var(--ac-rgb),.4)' }}>
          <PhoneCall className="h-6 w-6" />
        </span>
        <h1 style={{ fontSize: '2rem', fontWeight: 900, letterSpacing: '-0.03em', color: 'var(--tx-1)' }}>
          Your receptionist dashboard
        </h1>
        <p className="mx-auto mt-2 max-w-lg" style={{ color: 'var(--tx-2)' }}>
          Choose your business to see calls handled, bookings taken, and your agent’s status.
        </p>
      </motion.div>

      <form onSubmit={handleSubmit} className="relative mx-auto mt-8 max-w-lg">
        <Search className="pointer-events-none absolute left-3.5 top-1/2 h-4 w-4 -translate-y-1/2" style={{ color: 'var(--tx-3)' }} />
        <Input
          value={query}
          onChange={(e) => setQuery(e.target.value)}
          placeholder="Search your business by name or slug…"
          className="pl-10"
          aria-label="Search businesses"
        />
      </form>

      <div className="mx-auto mt-8 max-w-lg">
        {error && <Alert tone="error">{error}</Alert>}

        {!tenants && !error && (
          <div className="flex justify-center py-12">
            <Spinner className="text-[color:rgb(var(--ac-rgb))]" />
          </div>
        )}

        {tenants && filtered.length === 0 && (
          <div className="rounded-2xl px-6 py-10 text-center text-sm"
            style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)', color: 'var(--tx-3)' }}>
            {query ? 'No business matches that search.' : 'No businesses yet.'}
          </div>
        )}

        <div className="space-y-3">
          {filtered.map((t) => (
            <button
              key={t.id}
              onClick={() => navigate(`/portal/${t.slug}`)}
              className="card group flex w-full items-center gap-4 px-5 py-4 text-left transition-all hover:-translate-y-0.5"
              style={{ boxShadow: 'var(--shadow)' }}
            >
              <span className="flex h-11 w-11 shrink-0 items-center justify-center rounded-xl"
                style={{ background: 'rgba(var(--ac-rgb),.10)', border: '1px solid rgba(var(--ac-rgb),.2)' }}>
                <Building2 className="h-5 w-5" style={{ color: 'rgb(var(--ac-rgb))' }} />
              </span>
              <span className="min-w-0 flex-1">
                <span className="block truncate font-semibold" style={{ color: 'var(--tx-1)' }}>{t.business_name}</span>
                <span className="mt-1 flex items-center gap-2">
                  <Badge tone="slate">{t.category.replace('_', ' ')}</Badge>
                  <StatusPill status={t.status} />
                </span>
              </span>
              <ArrowRight className="h-4 w-4 shrink-0 transition-transform group-hover:translate-x-1" style={{ color: 'rgb(var(--ac-rgb))' }} />
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
