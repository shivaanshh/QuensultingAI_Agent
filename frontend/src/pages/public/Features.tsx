import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowRight, BarChart3, CalendarCheck, LayoutDashboard, ListChecks, PhoneCall,
  PhoneForwarded, ShieldAlert, Sliders, Sparkles, Clock,
} from 'lucide-react'
import { fadeUp, reveal, stagger } from '../../lib/motion'
import { AreaChart, DonutChart } from '../../components/ui/Charts'

const CONTAINER = 'w-full px-[clamp(1.25rem,4vw,3.5rem)]'
const DEMO = '/portal/demo-glow-salon'

const AGENT_FEATURES = [
  { icon: PhoneCall, title: 'Answers on the first ring', body: 'A named, natural-sounding agent picks up every call, 24/7 — no hold music, no voicemail.' },
  { icon: ShieldAlert, title: 'Urgent-call triage', body: 'Detects emergencies and urgent jobs and routes them exactly how your business needs.' },
  { icon: Clock, title: 'Availability-aware', body: 'Checks your real working hours before ever offering a slot, so it never overbooks.' },
  { icon: CalendarCheck, title: 'Books & confirms', body: 'Collects the details, confirms the appointment, and files it with a reference number.' },
  { icon: PhoneForwarded, title: 'Human handoff', body: 'Transfers to a real person the instant a caller asks — never a dead end.' },
  { icon: Sparkles, title: 'On-brand persona', body: 'A distinct voice and vocabulary tuned to your industry, speaking your services.' },
]

const DASH_FEATURES = [
  { icon: LayoutDashboard, title: 'Overview', body: 'Calls, bookings, answer rate, and caller sentiment — the whole front desk at a glance.' },
  { icon: CalendarCheck, title: 'Bookings', body: 'Every appointment the agent took. Search, filter, and mark them completed or cancelled.' },
  { icon: PhoneCall, title: 'Call log', body: 'Duration, outcome, sentiment, and the full transcript of every conversation.' },
  { icon: ListChecks, title: 'Services', body: 'Add, price, and toggle the services your receptionist offers — changes apply live.' },
  { icon: Sliders, title: 'Settings', body: 'Update hours, transfer number, notifications, and pause the agent anytime.' },
]

/* small non-interactive dashboard mock for the hero */
function DashboardPreview() {
  const calls = [2, 3, 1, 4, 3, 5, 4, 6, 5, 7, 6, 8, 7, 9]
  const bookings = [1, 1, 0, 2, 2, 3, 2, 3, 3, 4, 3, 5, 4, 6]
  return (
    <motion.div initial={{ opacity: 0, y: 20, scale: 0.97 }} animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.7, delay: 0.2, ease: [0.22, 1, 0.36, 1] }}
      className="overflow-hidden rounded-2xl" style={{ border: '1px solid var(--bd)', boxShadow: '0 32px 80px rgba(0,0,0,.22)', background: 'var(--bg-card)' }}>
      <div className="flex items-center gap-2 px-4 py-3" style={{ background: 'var(--bg-panel)', borderBottom: '1px solid var(--bd)' }}>
        <span className="h-3 w-3 rounded-full" style={{ background: '#FF5F57' }} />
        <span className="h-3 w-3 rounded-full" style={{ background: '#FFBD2E' }} />
        <span className="h-3 w-3 rounded-full" style={{ background: '#28CA41' }} />
        <span className="ml-2 text-xs font-semibold" style={{ color: 'var(--tx-3)' }}>Client portal · Overview</span>
      </div>
      <div className="space-y-3 p-4" style={{ background: 'var(--bg-main)' }}>
        <div className="grid grid-cols-4 gap-2">
          {[['128', 'Calls'], ['119', 'Answered'], ['74', 'Bookings'], ['58%', 'Rate']].map(([v, l]) => (
            <div key={l} className="rounded-lg p-2 text-center" style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)' }}>
              <p className="num text-lg font-bold" style={{ color: 'rgb(var(--ac-rgb))' }}>{v}</p>
              <p className="text-[10px]" style={{ color: 'var(--tx-3)' }}>{l}</p>
            </div>
          ))}
        </div>
        <div className="grid grid-cols-3 gap-2">
          <div className="col-span-2 rounded-lg p-2" style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)' }}>
            <AreaChart height={110} labels={calls.map((_, i) => String(i))}
              series={[
                { label: 'Calls', color: 'rgb(var(--ac-rgb))', values: calls },
                { label: 'Bookings', color: 'var(--ac-end)', values: bookings },
              ]} />
          </div>
          <div className="flex items-center justify-center rounded-lg p-2" style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)' }}>
            <DonutChart size={104} thickness={13} data={[
              { label: 'Positive', value: 82, color: 'var(--success)' },
              { label: 'Neutral', value: 30, color: 'var(--tx-3)' },
              { label: 'Negative', value: 6, color: 'var(--error)' },
            ]} />
          </div>
        </div>
      </div>
    </motion.div>
  )
}

export function Features() {
  return (
    <div style={{ background: 'var(--bg-main)', color: 'var(--tx-1)' }}>
      {/* HERO */}
      <section className="bg-hero relative overflow-hidden" style={{ borderBottom: '1px solid var(--bd)' }}>
        <div className={`${CONTAINER} grid grid-cols-1 items-center gap-14 py-20 lg:grid-cols-2`}>
          <motion.div variants={stagger} initial="initial" animate="animate">
            <motion.div variants={fadeUp} className="mb-6 inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-sm font-semibold"
              style={{ background: 'rgba(var(--ac-rgb),.10)', border: '1px solid rgba(var(--ac-rgb),.25)', color: 'rgb(var(--ac-rgb))' }}>
              <BarChart3 className="h-3.5 w-3.5" /> The product
            </motion.div>
            <motion.h1 variants={fadeUp} style={{ fontSize: 'clamp(2.3rem,4.8vw,3.4rem)', fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1.1, color: 'var(--tx-1)' }}>
              A receptionist that works —<br /><span className="gradient-text">and a dashboard that shows it.</span>
            </motion.h1>
            <motion.p variants={fadeUp} className="mt-6 max-w-xl text-[1.12rem]" style={{ color: 'var(--tx-2)', lineHeight: 1.7 }}>
              Your AI agent answers, triages, and books on every call. Behind it, a live dashboard turns
              those calls into bookings you can act on, transcripts you can read, and metrics you can trust.
            </motion.p>
            <motion.div variants={fadeUp} className="mt-9 flex flex-wrap gap-3">
              <Link to={DEMO} className="btn-primary inline-flex items-center gap-2 rounded-xl px-7 py-3 text-base">
                See a live dashboard <ArrowRight className="h-4 w-4" />
              </Link>
              <Link to="/contact" className="btn-ghost inline-flex items-center gap-2 rounded-xl px-6 py-3 text-base">Get started</Link>
            </motion.div>
          </motion.div>
          <DashboardPreview />
        </div>
      </section>

      {/* ON EVERY CALL */}
      <section className="py-24">
        <div className={CONTAINER}>
          <motion.div {...reveal} className="mb-14 text-center">
            <p className="mb-3 text-sm font-bold uppercase tracking-widest" style={{ color: 'rgb(var(--ac-rgb))' }}>On every call</p>
            <h2 style={{ fontSize: '2.3rem', fontWeight: 900, letterSpacing: '-0.03em', color: 'var(--tx-1)' }}>A full front desk, on the phone</h2>
          </motion.div>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {AGENT_FEATURES.map((f, i) => (
              <motion.div key={f.title} {...reveal} transition={{ ...reveal.transition, delay: i * 0.05 }}
                className="rounded-2xl p-6" style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)', boxShadow: 'var(--shadow)' }}>
                <span className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl"
                  style={{ background: 'rgba(var(--ac-rgb),.10)', border: '1px solid rgba(var(--ac-rgb),.2)' }}>
                  <f.icon className="h-5 w-5" style={{ color: 'rgb(var(--ac-rgb))' }} />
                </span>
                <h3 className="mb-1.5 font-bold" style={{ color: 'var(--tx-1)' }}>{f.title}</h3>
                <p className="text-sm" style={{ color: 'var(--tx-2)', lineHeight: 1.7 }}>{f.body}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* THE DASHBOARD */}
      <section className="py-24" style={{ background: 'var(--bg-panel)', borderTop: '1px solid var(--bd)', borderBottom: '1px solid var(--bd)' }}>
        <div className={CONTAINER}>
          <motion.div {...reveal} className="mb-14 text-center">
            <p className="mb-3 text-sm font-bold uppercase tracking-widest" style={{ color: 'rgb(var(--ac-rgb))' }}>Your dashboard</p>
            <h2 style={{ fontSize: '2.3rem', fontWeight: 900, letterSpacing: '-0.03em', color: 'var(--tx-1)' }}>Everything the agent did, in one place</h2>
            <p className="mx-auto mt-3 max-w-2xl text-[1.05rem]" style={{ color: 'var(--tx-2)' }}>
              A clean client portal for business owners — no training required.
            </p>
          </motion.div>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {DASH_FEATURES.map((f, i) => (
              <motion.div key={f.title} {...reveal} transition={{ ...reveal.transition, delay: i * 0.06 }}
                className="rounded-2xl p-6" style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)', boxShadow: 'var(--shadow)' }}>
                <span className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl"
                  style={{ background: 'rgba(var(--ac-rgb),.10)', border: '1px solid rgba(var(--ac-rgb),.2)' }}>
                  <f.icon className="h-5 w-5" style={{ color: 'rgb(var(--ac-rgb))' }} />
                </span>
                <h3 className="mb-1.5 font-bold" style={{ color: 'var(--tx-1)' }}>{f.title}</h3>
                <p className="text-sm" style={{ color: 'var(--tx-2)', lineHeight: 1.7 }}>{f.body}</p>
              </motion.div>
            ))}
          </div>
          <motion.div {...reveal} className="mt-12 text-center">
            <Link to={DEMO} className="btn-primary inline-flex items-center gap-2 rounded-xl px-7 py-3 text-base">
              Explore the live dashboard <ArrowRight className="h-4 w-4" />
            </Link>
            <p className="mt-3 text-sm" style={{ color: 'var(--tx-3)' }}>Sample data from a live demo salon — no signup.</p>
          </motion.div>
        </div>
      </section>

      {/* CTA */}
      <section className="py-20">
        <div className={`${CONTAINER} text-center`}>
          <motion.div {...reveal} className="mx-auto max-w-xl">
            <h2 style={{ fontSize: '1.9rem', fontWeight: 900, letterSpacing: '-0.03em', color: 'var(--tx-1)' }}>Ready to see it on your numbers?</h2>
            <p className="mt-3" style={{ fontSize: '1.05rem', color: 'var(--tx-2)' }}>We’ll stand up your receptionist and dashboard — usually within minutes.</p>
            <div className="mt-7 flex flex-wrap justify-center gap-3">
              <Link to="/contact" className="btn-primary inline-flex items-center gap-2 rounded-xl px-7 py-3 text-base">Get started <ArrowRight className="h-4 w-4" /></Link>
              <Link to="/pricing" className="btn-ghost inline-flex items-center gap-2 rounded-xl px-6 py-3 text-base">See pricing</Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}
