import { useId } from 'react'

/**
 * Lightweight, dependency-free SVG charts driven by the token palette.
 * They read colors from CSS vars so they follow the light/dark theme.
 */

interface Series {
  label: string
  color: string // a CSS color, e.g. 'rgb(var(--ac-rgb))'
  values: number[]
}

/** Layered area/line chart — used for the calls vs bookings trend. */
export function AreaChart({
  series,
  labels,
  height = 180,
}: {
  series: Series[]
  labels: string[]
  height?: number
}) {
  const gid = useId().replace(/:/g, '')
  const W = 640
  const H = height
  const padX = 8
  const padY = 12
  const n = Math.max(1, labels.length)
  const max = Math.max(1, ...series.flatMap((s) => s.values))
  const x = (i: number) => padX + (i * (W - padX * 2)) / Math.max(1, n - 1)
  const y = (v: number) => padY + (1 - v / max) * (H - padY * 2)

  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={height} preserveAspectRatio="none" role="img" aria-label="Trend chart">
      {/* horizontal gridlines */}
      {[0.25, 0.5, 0.75].map((f) => (
        <line key={f} x1={padX} x2={W - padX} y1={padY + f * (H - padY * 2)} y2={padY + f * (H - padY * 2)}
          stroke="var(--bd)" strokeWidth="1" strokeDasharray="3 4" />
      ))}
      {series.map((s, si) => {
        const pts = s.values.map((v, i) => `${x(i)},${y(v)}`).join(' ')
        const area = `M ${x(0)},${H - padY} L ${s.values.map((v, i) => `${x(i)},${y(v)}`).join(' L ')} L ${x(n - 1)},${H - padY} Z`
        return (
          <g key={s.label}>
            <defs>
              <linearGradient id={`${gid}-${si}`} x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor={s.color} stopOpacity="0.22" />
                <stop offset="100%" stopColor={s.color} stopOpacity="0" />
              </linearGradient>
            </defs>
            <path d={area} fill={`url(#${gid}-${si})`} />
            <polyline points={pts} fill="none" stroke={s.color} strokeWidth="2" strokeLinejoin="round" strokeLinecap="round" />
            {/* emphasise the final point */}
            {s.values.length > 0 && (
              <circle cx={x(n - 1)} cy={y(s.values[s.values.length - 1])} r="3.5" fill={s.color} />
            )}
          </g>
        )
      })}
    </svg>
  )
}

/** Simple vertical bar chart. */
export function BarChart({ values, color, height = 120 }: { values: number[]; color: string; height?: number }) {
  const W = 640
  const H = height
  const n = Math.max(1, values.length)
  const max = Math.max(1, ...values)
  const gap = 3
  const bw = (W - gap * (n - 1)) / n
  return (
    <svg viewBox={`0 0 ${W} ${H}`} width="100%" height={height} preserveAspectRatio="none" role="img" aria-label="Bar chart">
      {values.map((v, i) => {
        const h = (v / max) * (H - 6)
        return <rect key={i} x={i * (bw + gap)} y={H - h} width={bw} height={h} rx={Math.min(3, bw / 2)} fill={color}
          opacity={0.55 + 0.45 * (v / max)} />
      })}
    </svg>
  )
}

/** Donut / ring chart for categorical breakdowns (e.g. sentiment). */
export function DonutChart({
  data,
  size = 132,
  thickness = 16,
}: {
  data: { label: string; value: number; color: string }[]
  size?: number
  thickness?: number
}) {
  const total = data.reduce((s, d) => s + d.value, 0)
  const r = (size - thickness) / 2
  const cx = size / 2
  const cy = size / 2
  const circ = 2 * Math.PI * r
  let offset = 0
  return (
    <svg viewBox={`0 0 ${size} ${size}`} width={size} height={size} role="img" aria-label="Breakdown chart">
      <circle cx={cx} cy={cy} r={r} fill="none" stroke="var(--bd)" strokeWidth={thickness} />
      {total > 0 &&
        data.map((d) => {
          const frac = d.value / total
          const dash = frac * circ
          const seg = (
            <circle
              key={d.label}
              cx={cx}
              cy={cy}
              r={r}
              fill="none"
              stroke={d.color}
              strokeWidth={thickness}
              strokeDasharray={`${dash} ${circ - dash}`}
              strokeDashoffset={-offset}
              transform={`rotate(-90 ${cx} ${cy})`}
              strokeLinecap="butt"
            />
          )
          offset += dash
          return seg
        })}
      <text x={cx} y={cy - 2} textAnchor="middle" fontSize="22" fontWeight="800" fill="var(--tx-1)" fontFamily="inherit">
        {total}
      </text>
      <text x={cx} y={cy + 16} textAnchor="middle" fontSize="10" fill="var(--tx-3)" fontFamily="inherit">
        calls
      </text>
    </svg>
  )
}
