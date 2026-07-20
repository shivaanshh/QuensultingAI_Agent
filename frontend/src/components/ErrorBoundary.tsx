import { Component, type ErrorInfo, type ReactNode } from 'react'

interface Props {
  children: ReactNode
}
interface State {
  error: Error | null
}

/** Catches render/runtime errors anywhere below it so a single bad component
 *  shows a friendly recovery screen instead of a blank white page. */
export class ErrorBoundary extends Component<Props, State> {
  state: State = { error: null }

  static getDerivedStateFromError(error: Error): State {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('Unhandled UI error:', error, info)
  }

  render() {
    if (!this.state.error) return this.props.children
    return (
      <div
        style={{
          minHeight: '100vh',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          background: 'var(--bg-main)',
          color: 'var(--tx-1)',
          padding: '2rem',
          fontFamily: 'system-ui, -apple-system, sans-serif',
        }}
      >
        <div style={{ maxWidth: 420, textAlign: 'center' }}>
          <div
            style={{
              width: 52,
              height: 52,
              margin: '0 auto 1.25rem',
              borderRadius: 14,
              display: 'grid',
              placeItems: 'center',
              color: '#fff',
              background: 'linear-gradient(135deg, rgb(var(--ac-rgb)), var(--ac-end))',
            }}
          >
            <svg viewBox="0 0 24 24" width="24" height="24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
              <path d="M10.29 3.86 1.82 18a2 2 0 0 0 1.71 3h16.94a2 2 0 0 0 1.71-3L13.71 3.86a2 2 0 0 0-3.42 0z" />
              <path d="M12 9v4M12 17h.01" />
            </svg>
          </div>
          <h1 style={{ fontSize: '1.4rem', fontWeight: 800, letterSpacing: '-0.02em', margin: 0 }}>Something went wrong</h1>
          <p style={{ color: 'var(--tx-2)', marginTop: '0.6rem', lineHeight: 1.6 }}>
            The page hit an unexpected error. Reloading usually clears it. If it keeps happening, let us know.
          </p>
          <div style={{ marginTop: '1.5rem', display: 'flex', gap: '0.75rem', justifyContent: 'center', flexWrap: 'wrap' }}>
            <button
              onClick={() => window.location.reload()}
              className="btn-primary"
              style={{ padding: '0.6rem 1.4rem', borderRadius: '0.7rem' }}
            >
              Reload page
            </button>
            <a
              href="/"
              className="btn-ghost"
              style={{ padding: '0.6rem 1.4rem', borderRadius: '0.7rem', textDecoration: 'none', display: 'inline-flex', alignItems: 'center' }}
            >
              Back to home
            </a>
          </div>
        </div>
      </div>
    )
  }
}
