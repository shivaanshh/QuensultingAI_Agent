import { Link, NavLink, Outlet } from 'react-router-dom'
import { LayoutGrid, Moon, PhoneCall, Plus, ShieldAlert, Sun } from 'lucide-react'
import { useTheme } from '../../lib/theme'

function navLinkStyle({ isActive }: { isActive: boolean }) {
  return {
    fontWeight: isActive ? 600 : 500,
    color: isActive ? 'rgb(var(--ac-rgb))' : 'var(--tx-2)',
    background: isActive ? 'rgba(var(--ac-rgb),.10)' : 'transparent',
  }
}

export function AdminLayout() {
  const { theme, toggle } = useTheme()
  const isDark = theme === 'dark'

  return (
    <div className="flex min-h-screen" style={{ background: 'var(--bg-main)', color: 'var(--tx-1)' }}>
      <aside className="flex w-60 shrink-0 flex-col" style={{ background: 'var(--bg-panel)', borderRight: '1px solid var(--bd)' }}>
        <Link to="/admin" className="flex items-center gap-2.5 px-5 py-4" style={{ borderBottom: '1px solid var(--bd)' }}>
          <span className="flex h-9 w-9 items-center justify-center rounded-xl text-white"
            style={{ background: 'linear-gradient(135deg, rgb(var(--ac-rgb)), var(--ac-end))', boxShadow: '0 4px 14px rgba(var(--ac-rgb),.4)' }}>
            <PhoneCall size={17} />
          </span>
          <div>
            <p className="text-sm font-black leading-tight text-[color:var(--tx-1)]">
              Quensulting<span style={{ color: 'rgb(var(--ac-rgb))' }}>AI</span>
            </p>
            <p className="text-[0.7rem] font-semibold uppercase tracking-wider" style={{ color: 'var(--tx-3)' }}>Admin console</p>
          </div>
        </Link>

        <nav className="flex-1 space-y-1 px-3 py-4">
          <NavLink to="/admin" end className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors" style={navLinkStyle}>
            <LayoutGrid size={16} /> Tenants
          </NavLink>
          <NavLink to="/admin/new" className="flex items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors" style={navLinkStyle}>
            <Plus size={16} /> New tenant
          </NavLink>
        </nav>

        <div className="space-y-1 px-3 pb-4">
          <button onClick={toggle}
            className="flex w-full items-center gap-2.5 rounded-lg px-3 py-2 text-sm transition-colors"
            style={{ color: 'var(--tx-2)' }}>
            {isDark ? <Sun size={16} /> : <Moon size={16} />}
            {isDark ? 'Light mode' : 'Dark mode'}
          </button>
          <Link to="/" className="block rounded-lg px-3 py-2 text-sm transition-colors" style={{ color: 'var(--tx-3)' }}>
            ← Back to site
          </Link>
        </div>
      </aside>

      <div className="flex flex-1 flex-col">
        <div className="flex items-center gap-2 px-6 py-2 text-xs"
          style={{ background: 'rgba(245,158,11,.12)', color: 'var(--warning)', borderBottom: '1px solid rgba(245,158,11,.25)' }}>
          <ShieldAlert size={14} />
          Internal admin — this build has no authentication. Do not share this URL publicly.
        </div>
        <main className="flex-1 p-6 lg:p-8">
          <Outlet />
        </main>
      </div>
    </div>
  )
}
