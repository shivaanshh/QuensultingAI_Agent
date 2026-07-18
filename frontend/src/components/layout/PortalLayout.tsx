import { Link, Outlet, useNavigate } from 'react-router-dom'
import { ArrowLeft, Moon, PhoneCall, Sun } from 'lucide-react'
import { useTheme } from '../../lib/theme'

const CONTAINER = 'w-full px-[clamp(1.25rem,4vw,3rem)]'

export function PortalLayout() {
  const { theme, toggle } = useTheme()
  const navigate = useNavigate()
  const isDark = theme === 'dark'

  return (
    <div className="flex min-h-screen flex-col" style={{ background: 'var(--bg-main)', color: 'var(--tx-1)' }}>
      <header
        className="sticky top-0 z-50 flex h-[64px] items-center"
        style={{ background: 'var(--bg-panel)', borderBottom: '1px solid var(--bd)' }}
      >
        <div className={`${CONTAINER} flex items-center gap-4`}>
          <Link to="/portal" className="flex items-center gap-2.5">
            <span className="flex h-9 w-9 items-center justify-center rounded-xl text-white"
              style={{ background: 'linear-gradient(135deg, rgb(var(--ac-rgb)), var(--ac-end))', boxShadow: '0 4px 14px rgba(var(--ac-rgb),.4)' }}>
              <PhoneCall size={17} />
            </span>
            <span className="flex items-center gap-2">
              <span className="text-[1.05rem] font-black tracking-tight text-[color:var(--tx-1)]">
                Quensulting<span style={{ color: 'rgb(var(--ac-rgb))' }}>AI</span>
              </span>
              <span className="hidden rounded-full px-2.5 py-0.5 text-[0.7rem] font-bold sm:inline-flex"
                style={{ background: 'rgba(var(--ac-rgb),.12)', color: 'rgb(var(--ac-rgb))', border: '1px solid rgba(var(--ac-rgb),.25)' }}>
                Client portal
              </span>
            </span>
          </Link>

          <div className="ml-auto flex items-center gap-2.5">
            <button onClick={() => navigate('/portal')}
              className="btn-ghost hidden items-center gap-1.5 rounded-lg px-3.5 py-2 text-sm sm:inline-flex">
              Switch business
            </button>
            <button onClick={toggle}
              className="flex h-9 w-9 items-center justify-center rounded-lg"
              style={{ background: 'var(--bg-raised)', border: '1px solid var(--bd)', color: 'var(--tx-2)' }}
              title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}>
              {isDark ? <Sun size={16} /> : <Moon size={16} />}
            </button>
            <Link to="/" className="btn-ghost inline-flex items-center gap-1.5 rounded-lg px-3.5 py-2 text-sm">
              <ArrowLeft size={14} /> Site
            </Link>
          </div>
        </div>
      </header>

      <main className="flex-1">
        <div className={`${CONTAINER} py-8`}>
          <Outlet />
        </div>
      </main>
    </div>
  )
}
