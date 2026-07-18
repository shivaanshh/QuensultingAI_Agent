import { useCallback, useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useOutletContext, useParams } from 'react-router-dom'
import {
  ArrowLeft, CalendarCheck, LayoutDashboard, ListChecks, Moon, Phone, PhoneCall,
  Settings as SettingsIcon, Sun,
} from 'lucide-react'
import { api, ApiError } from '../../api/client'
import type { TenantDetail } from '../../api/types'
import { useTheme } from '../../lib/theme'
import { StatusPill } from '../ui/Badge'
import { Alert } from '../ui/Alert'
import { Spinner } from '../ui/Spinner'

export interface PortalContext {
  tenant: TenantDetail
  reload: () => void
}

export function usePortal() {
  return useOutletContext<PortalContext>()
}

const NAV = [
  { to: '', label: 'Overview', icon: LayoutDashboard, end: true },
  { to: 'bookings', label: 'Bookings', icon: CalendarCheck, end: false },
  { to: 'calls', label: 'Calls', icon: Phone, end: false },
  { to: 'services', label: 'Services', icon: ListChecks, end: false },
  { to: 'settings', label: 'Settings', icon: SettingsIcon, end: false },
]

export function PortalShell() {
  const { slug = '' } = useParams()
  const { theme, toggle } = useTheme()
  const isDark = theme === 'dark'
  const [tenant, setTenant] = useState<TenantDetail | null>(null)
  const [error, setError] = useState<string | null>(null)

  const reload = useCallback(() => {
    api
      .getTenant(slug)
      .then(setTenant)
      .catch((err) => setError(err instanceof ApiError ? err.message : 'Failed to load dashboard'))
  }, [slug])

  useEffect(() => {
    setTenant(null)
    setError(null)
    reload()
  }, [reload])

  const base = `/portal/${slug}`
  const live = tenant ? Boolean(tenant.retell_agent_id) && tenant.status === 'active' : false

  return (
    <div className="flex min-h-screen" style={{ background: 'var(--bg-main)', color: 'var(--tx-1)' }}>
      {/* sidebar (desktop) */}
      <aside className="hidden w-60 shrink-0 flex-col md:flex" style={{ background: 'var(--bg-panel)', borderRight: '1px solid var(--bd)' }}>
        <Link to="/portal" className="flex items-center gap-2.5 px-5 py-4" style={{ borderBottom: '1px solid var(--bd)' }}>
          <span className="flex h-9 w-9 items-center justify-center rounded-xl text-white"
            style={{ background: 'linear-gradient(135deg, rgb(var(--ac-rgb)), var(--ac-end))', boxShadow: '0 4px 14px rgba(var(--ac-rgb),.4)' }}>
            <PhoneCall size={17} />
          </span>
          <div className="min-w-0">
            <p className="truncate text-sm font-bold text-[color:var(--tx-1)]">{tenant?.business_name ?? 'Dashboard'}</p>
            <p className="text-[0.7rem] font-semibold uppercase tracking-wider" style={{ color: 'var(--tx-3)' }}>Client portal</p>
          </div>
        </Link>

        <nav className="flex-1 space-y-1 px-3 py-4">
          {NAV.map((item) => (
            <NavLink key={item.label} to={`${base}/${item.to}`.replace(/\/$/, '')} end={item.end}
              className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors"
              style={({ isActive }) => ({
                fontWeight: isActive ? 600 : 500,
                color: isActive ? 'rgb(var(--ac-rgb))' : 'var(--tx-2)',
                background: isActive ? 'rgba(var(--ac-rgb),.10)' : 'transparent',
              })}>
              <item.icon size={16} /> {item.label}
            </NavLink>
          ))}
        </nav>

        <div className="space-y-1 px-3 pb-4">
          <button onClick={toggle} className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm" style={{ color: 'var(--tx-2)' }}>
            {isDark ? <Sun size={16} /> : <Moon size={16} />} {isDark ? 'Light mode' : 'Dark mode'}
          </button>
          <Link to="/portal" className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm" style={{ color: 'var(--tx-3)' }}>
            <ArrowLeft size={15} /> Switch business
          </Link>
        </div>
      </aside>

      <div className="flex min-w-0 flex-1 flex-col">
        {/* top bar */}
        <header className="sticky top-0 z-40 flex h-[60px] items-center gap-3 px-4 lg:px-8"
          style={{ background: 'color-mix(in srgb, var(--bg-panel) 85%, transparent)', backdropFilter: 'blur(12px)', borderBottom: '1px solid var(--bd)' }}>
          <Link to="/portal" className="flex items-center gap-2 md:hidden">
            <span className="flex h-8 w-8 items-center justify-center rounded-lg text-white"
              style={{ background: 'linear-gradient(135deg, rgb(var(--ac-rgb)), var(--ac-end))' }}>
              <PhoneCall size={15} />
            </span>
          </Link>
          <div className="min-w-0">
            <p className="truncate text-sm font-semibold text-[color:var(--tx-1)] md:hidden">{tenant?.business_name ?? ''}</p>
          </div>
          <div className="ml-auto flex items-center gap-2.5">
            {tenant && (
              <span className="hidden items-center gap-2 rounded-full px-3 py-1.5 text-xs font-semibold sm:inline-flex"
                style={live
                  ? { background: 'rgba(16,185,129,.12)', color: 'var(--success)', border: '1px solid rgba(16,185,129,.25)' }
                  : { background: 'rgba(245,158,11,.14)', color: 'var(--warning)', border: '1px solid rgba(245,158,11,.28)' }}>
                <span className="h-2 w-2 rounded-full" style={{ background: live ? 'var(--success)' : 'var(--warning)' }} />
                {live ? 'Answering calls' : 'Agent offline'}
              </span>
            )}
            <button onClick={toggle} className="flex h-9 w-9 items-center justify-center rounded-lg md:hidden"
              style={{ background: 'var(--bg-raised)', border: '1px solid var(--bd)', color: 'var(--tx-2)' }}>
              {isDark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <Link to="/" className="btn-ghost hidden items-center gap-1.5 rounded-lg px-3 py-2 text-sm sm:inline-flex">Site</Link>
          </div>
        </header>

        {/* mobile nav */}
        <nav className="flex gap-1 overflow-x-auto px-3 py-2 md:hidden" style={{ borderBottom: '1px solid var(--bd)', background: 'var(--bg-panel)' }}>
          {NAV.map((item) => (
            <NavLink key={item.label} to={`${base}/${item.to}`.replace(/\/$/, '')} end={item.end}
              className="flex shrink-0 items-center gap-1.5 rounded-lg px-3 py-1.5 text-sm"
              style={({ isActive }) => ({
                fontWeight: isActive ? 600 : 500,
                color: isActive ? 'rgb(var(--ac-rgb))' : 'var(--tx-2)',
                background: isActive ? 'rgba(var(--ac-rgb),.10)' : 'transparent',
              })}>
              <item.icon size={15} /> {item.label}
            </NavLink>
          ))}
        </nav>

        <main className="flex-1 p-4 lg:p-8">
          {error && <Alert tone="error">{error}</Alert>}
          {!tenant && !error && (
            <div className="flex justify-center py-24">
              <Spinner className="text-[color:rgb(var(--ac-rgb))]" />
            </div>
          )}
          {tenant && (
            <div className="mx-auto max-w-6xl">
              <div className="mb-6 flex flex-wrap items-center gap-3">
                <h1 style={{ fontSize: '1.6rem', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--tx-1)' }}>
                  {tenant.business_name}
                </h1>
                <StatusPill status={tenant.status} />
              </div>
              <Outlet context={{ tenant, reload } satisfies PortalContext} />
            </div>
          )}
        </main>
      </div>
    </div>
  )
}
