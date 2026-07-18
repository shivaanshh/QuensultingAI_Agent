import { useEffect, useState } from 'react'
import { Link, NavLink, Outlet, useNavigate } from 'react-router-dom'
import { ArrowRight, Moon, PhoneCall, Sun } from 'lucide-react'
import { useTheme } from '../../lib/theme'

const NAV_LINKS = [
  { label: 'Home', to: '/' },
  { label: 'Features', to: '/features' },
  { label: 'Pricing', to: '/pricing' },
  { label: 'About', to: '/about' },
  { label: 'Contact', to: '/contact' },
]

const CONTAINER = 'w-full px-[clamp(1.25rem,4vw,3.5rem)]'

function BrandMark({ size = 38 }: { size?: number }) {
  return (
    <span
      className="flex items-center justify-center rounded-xl text-white shrink-0"
      style={{
        width: size,
        height: size,
        background: 'linear-gradient(135deg, rgb(var(--ac-rgb)), var(--ac-end))',
        boxShadow: '0 4px 16px rgba(var(--ac-rgb),.45)',
      }}
    >
      <PhoneCall size={size * 0.5} />
    </span>
  )
}

function Header() {
  const { theme, toggle } = useTheme()
  const navigate = useNavigate()
  const [scrolled, setScrolled] = useState(false)
  const isDark = theme === 'dark'

  useEffect(() => {
    const fn = () => setScrolled(window.scrollY > 12)
    window.addEventListener('scroll', fn, { passive: true })
    return () => window.removeEventListener('scroll', fn)
  }, [])

  return (
    <header
      className="sticky top-0 z-50 flex h-[68px] items-center"
      style={{
        backdropFilter: 'blur(16px)',
        WebkitBackdropFilter: 'blur(16px)',
        background: scrolled ? 'color-mix(in srgb, var(--bg-panel) 85%, transparent)' : 'transparent',
        borderBottom: `1px solid ${scrolled ? 'var(--bd)' : 'transparent'}`,
        boxShadow: scrolled ? 'var(--shadow)' : 'none',
        transition: 'background .25s, border-color .25s, box-shadow .25s',
      }}
    >
      <div className={`${CONTAINER} flex items-center gap-6`}>
        <Link to="/" className="flex items-center gap-2.5 shrink-0">
          <BrandMark />
          <span className="text-[1.15rem] font-black tracking-tight text-[color:var(--tx-1)]">
            Quensulting<span style={{ color: 'rgb(var(--ac-rgb))' }}>AI</span>
          </span>
          <span
            className="hidden sm:inline-flex rounded-full px-2.5 py-1 text-[0.72rem] font-bold"
            style={{
              background: 'rgba(var(--ac-rgb),.12)',
              color: 'rgb(var(--ac-rgb))',
              border: '1px solid rgba(var(--ac-rgb),.25)',
            }}
          >
            Receptionist
          </span>
        </Link>

        <div className="hidden md:block h-6 w-px shrink-0" style={{ background: 'var(--bd)' }} />

        <nav className="hidden md:flex flex-1 items-center gap-1">
          {NAV_LINKS.map(({ label, to }) => (
            <NavLink
              key={label}
              to={to}
              end={to === '/'}
              className="rounded-lg px-4 py-2 text-[0.95rem] transition-colors"
              style={({ isActive }) => ({
                fontWeight: isActive ? 700 : 500,
                color: isActive ? 'rgb(var(--ac-rgb))' : 'var(--tx-2)',
                background: isActive ? 'rgba(var(--ac-rgb),.10)' : 'transparent',
              })}
            >
              {label}
            </NavLink>
          ))}
        </nav>

        <div className="ml-auto flex items-center gap-2.5 shrink-0">
          <button
            onClick={toggle}
            title={isDark ? 'Switch to light mode' : 'Switch to dark mode'}
            className="flex h-9 w-9 items-center justify-center rounded-lg transition-colors"
            style={{ background: 'var(--bg-raised)', border: '1px solid var(--bd)', color: 'var(--tx-2)' }}
          >
            {isDark ? <Sun size={16} /> : <Moon size={16} />}
          </button>
          <button
            onClick={() => navigate('/portal')}
            className="btn-ghost hidden sm:inline-flex items-center gap-1.5 rounded-lg px-4 py-2 text-[0.95rem]"
          >
            Client login
          </button>
          <button
            onClick={() => navigate('/contact')}
            className="btn-primary inline-flex items-center gap-1.5 rounded-lg px-4 py-2 text-[0.95rem]"
          >
            Get started <ArrowRight size={15} />
          </button>
        </div>
      </div>
    </header>
  )
}

function Footer() {
  const cols = [
    { title: 'Product', links: [{ label: 'Features', to: '/features' }, { label: 'Pricing', to: '/pricing' }, { label: 'About', to: '/about' }, { label: 'Contact', to: '/contact' }] },
    { title: 'Access', links: [{ label: 'Client portal', to: '/portal' }, { label: 'Admin console', to: '/admin' }] },
    {
      title: 'Built with',
      links: [
        { label: 'RetellAI voice agents', to: null },
        { label: 'FastAPI backend', to: null },
        { label: 'React + Vite', to: null },
      ],
    },
  ]

  return (
    <footer style={{ background: 'var(--bg-panel)', borderTop: '1px solid var(--bd)' }}>
      <div className={`${CONTAINER} grid gap-10 pt-16 pb-8 md:grid-cols-[2fr_1fr_1fr_1fr]`}>
        <div>
          <div className="mb-4 flex items-center gap-2.5">
            <BrandMark size={34} />
            <span className="text-[1.1rem] font-black tracking-tight text-[color:var(--tx-1)]">
              Quensulting<span style={{ color: 'rgb(var(--ac-rgb))' }}>AI</span>
            </span>
          </div>
          <p className="mb-5 max-w-[280px] text-[0.95rem] leading-relaxed text-[color:var(--tx-2)]">
            AI voice receptionists that answer every call, triage the urgent ones, and book
            appointments around the clock — for any kind of business.
          </p>
          <span
            className="inline-flex items-center gap-2 rounded-full px-3 py-1.5 text-[0.82rem] font-bold"
            style={{ background: 'rgba(16,185,129,.12)', color: 'var(--success)', border: '1px solid rgba(16,185,129,.25)' }}
          >
            <span className="h-2 w-2 rounded-full" style={{ background: 'var(--success)' }} />
            Platform live
          </span>
        </div>

        {cols.map((col) => (
          <div key={col.title}>
            <h4 className="mb-4 text-[0.72rem] font-extrabold uppercase tracking-widest text-[color:var(--tx-3)]">
              {col.title}
            </h4>
            <ul className="flex flex-col gap-2.5">
              {col.links.map(({ label, to }) => (
                <li key={label}>
                  {to ? (
                    <Link to={to} className="text-[0.95rem] text-[color:var(--tx-2)] transition-colors hover:text-[color:var(--tx-1)]">
                      {label}
                    </Link>
                  ) : (
                    <span className="text-[0.95rem] text-[color:var(--tx-3)]">{label}</span>
                  )}
                </li>
              ))}
            </ul>
          </div>
        ))}
      </div>

      <div
        className={`${CONTAINER} flex flex-wrap items-center justify-between gap-3 py-6`}
        style={{ borderTop: '1px solid var(--bd)' }}
      >
        <p className="text-[0.85rem] text-[color:var(--tx-3)]">
          © {new Date().getFullYear()} QuensultingAI. All rights reserved.
        </p>
        <p className="text-[0.85rem] text-[color:var(--tx-3)]">Built with RetellAI · FastAPI · React</p>
      </div>
    </footer>
  )
}

export function PublicLayout() {
  return (
    <div className="flex min-h-screen flex-col" style={{ background: 'var(--bg-main)', color: 'var(--tx-1)' }}>
      <Header />
      <main className="flex-1">
        <Outlet />
      </main>
      <Footer />
    </div>
  )
}
