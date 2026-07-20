import { Link } from 'react-router-dom'
import { Compass, Home } from 'lucide-react'

export function NotFound() {
  return (
    <div className="flex items-center justify-center px-6 py-24" style={{ minHeight: '60vh' }}>
      <div className="text-center">
        <span className="mx-auto mb-6 flex h-16 w-16 items-center justify-center rounded-2xl text-white"
          style={{ background: 'linear-gradient(135deg, rgb(var(--ac-rgb)), var(--ac-end))', boxShadow: '0 12px 34px rgba(var(--ac-rgb),.4)' }}>
          <Compass className="h-7 w-7" />
        </span>
        <p className="num font-black" style={{ fontSize: '3rem', lineHeight: 1, letterSpacing: '-0.04em', color: 'rgb(var(--ac-rgb))' }}>404</p>
        <h1 className="mt-2" style={{ fontSize: '1.5rem', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--tx-1)' }}>
          This page took a wrong turn
        </h1>
        <p className="mx-auto mt-2 max-w-sm" style={{ color: 'var(--tx-2)' }}>
          The page you’re looking for doesn’t exist or may have moved.
        </p>
        <div className="mt-7 flex flex-wrap justify-center gap-3">
          <Link to="/" className="btn-primary inline-flex items-center gap-2 rounded-xl px-6 py-3">
            <Home size={16} /> Back to home
          </Link>
          <Link to="/portal" className="btn-ghost inline-flex items-center gap-2 rounded-xl px-6 py-3">
            Client portal
          </Link>
        </div>
      </div>
    </div>
  )
}
