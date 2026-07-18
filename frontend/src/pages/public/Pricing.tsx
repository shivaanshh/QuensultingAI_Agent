import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import { ArrowRight, Check, Sparkles } from 'lucide-react'
import { fadeUp, reveal, stagger } from '../../lib/motion'

const CONTAINER = 'w-full px-[clamp(1.25rem,4vw,3.5rem)]'

const PLANS = [
  {
    name: 'Starter',
    price: 99,
    tagline: 'For a single location testing the waters.',
    minutes: '500 call-minutes / mo',
    overage: 'then $0.35 / min',
    highlight: false,
    features: ['1 phone number', 'Web chat included', 'Bookings + call log', 'Email notifications', 'Dashboard access'],
  },
  {
    name: 'Growth',
    price: 249,
    tagline: 'For a busy practice that can’t miss a call.',
    minutes: '1,500 call-minutes / mo',
    overage: 'then $0.30 / min',
    highlight: true,
    features: ['Everything in Starter', 'Priority call routing', 'Urgent-call triage tuning', 'Sentiment analytics', 'Up to 2 numbers'],
  },
  {
    name: 'Business',
    price: 599,
    tagline: 'For multi-location or high call volume.',
    minutes: '4,000 call-minutes / mo',
    overage: 'then $0.25 / min',
    highlight: false,
    features: ['Everything in Growth', 'Multiple numbers', 'Custom persona & voice', 'Priority support', 'Onboarding help'],
  },
]

const FAQ = [
  { q: 'What counts as a call-minute?', a: 'Only the time your agent is actually on a live call, billed to the second. Missed or silent calls don’t count.' },
  { q: 'Is web chat really included?', a: 'Yes — a text version of the same agent runs on your site at no extra per-message charge on every plan.' },
  { q: 'Do I need to buy hardware or a new phone system?', a: 'No. We attach your AI agent to a phone number and it just works. Keep your existing line or get a new one.' },
  { q: 'Can I change plans or cancel?', a: 'Anytime. Plans are month-to-month, and you can pause your receptionist from the dashboard whenever you like.' },
]

export function Pricing() {
  return (
    <div style={{ background: 'var(--bg-main)', color: 'var(--tx-1)' }}>
      {/* HERO */}
      <section className="bg-hero" style={{ borderBottom: '1px solid var(--bd)' }}>
        <div className={`${CONTAINER} py-20 text-center`}>
          <motion.div variants={stagger} initial="initial" animate="animate">
            <motion.div variants={fadeUp} className="mb-6 inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-sm font-semibold"
              style={{ background: 'rgba(var(--ac-rgb),.10)', border: '1px solid rgba(var(--ac-rgb),.25)', color: 'rgb(var(--ac-rgb))' }}>
              <Sparkles className="h-3.5 w-3.5" /> Simple, usage-based pricing
            </motion.div>
            <motion.h1 variants={fadeUp} style={{ fontSize: 'clamp(2.3rem,4.8vw,3.4rem)', fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1.1, color: 'var(--tx-1)' }}>
              Pay for calls answered,<br /><span className="gradient-text">not seats or setup.</span>
            </motion.h1>
            <motion.p variants={fadeUp} className="mx-auto mt-5 max-w-xl text-[1.1rem]" style={{ color: 'var(--tx-2)', lineHeight: 1.7 }}>
              A flat monthly plan with included call-minutes, then simple per-minute overage. Web chat is
              included on every tier. No hardware, no contracts.
            </motion.p>
          </motion.div>
        </div>
      </section>

      {/* PLANS */}
      <section className="py-20">
        <div className={CONTAINER}>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-3">
            {PLANS.map((p, i) => (
              <motion.div key={p.name} {...reveal} transition={{ ...reveal.transition, delay: i * 0.08 }}
                className="relative flex flex-col rounded-2xl p-7"
                style={{
                  background: 'var(--bg-card)',
                  border: p.highlight ? '1.5px solid rgb(var(--ac-rgb))' : '1px solid var(--bd)',
                  boxShadow: p.highlight ? '0 20px 50px rgba(var(--ac-rgb),.16)' : 'var(--shadow)',
                }}>
                {p.highlight && (
                  <span className="absolute -top-3 left-7 rounded-full px-3 py-1 text-xs font-bold text-white"
                    style={{ background: 'linear-gradient(135deg, rgb(var(--ac-rgb)), var(--ac-end))' }}>
                    Most popular
                  </span>
                )}
                <h3 className="font-bold" style={{ fontSize: '1.2rem', color: 'var(--tx-1)' }}>{p.name}</h3>
                <p className="mt-1 text-sm" style={{ color: 'var(--tx-3)' }}>{p.tagline}</p>
                <div className="mt-5 flex items-baseline gap-1">
                  <span className="num font-black" style={{ fontSize: '2.6rem', letterSpacing: '-0.03em', color: 'var(--tx-1)' }}>${p.price}</span>
                  <span className="text-sm" style={{ color: 'var(--tx-3)' }}>/ month</span>
                </div>
                <p className="num mt-1 text-sm font-semibold" style={{ color: 'rgb(var(--ac-rgb))' }}>{p.minutes}</p>
                <p className="num text-xs" style={{ color: 'var(--tx-3)' }}>{p.overage}</p>
                <ul className="mt-6 flex-1 space-y-2.5">
                  {p.features.map((f) => (
                    <li key={f} className="flex items-start gap-2 text-sm" style={{ color: 'var(--tx-2)' }}>
                      <Check className="mt-0.5 h-4 w-4 shrink-0" style={{ color: 'var(--success)' }} /> {f}
                    </li>
                  ))}
                </ul>
                <Link to="/contact"
                  className={p.highlight
                    ? 'btn-primary mt-7 inline-flex w-full items-center justify-center gap-2 rounded-xl px-6 py-3'
                    : 'btn-ghost mt-7 inline-flex w-full items-center justify-center gap-2 rounded-xl px-6 py-3'}>
                  Get started <ArrowRight className="h-4 w-4" />
                </Link>
              </motion.div>
            ))}
          </div>
          <p className="mt-8 text-center text-sm" style={{ color: 'var(--tx-3)' }}>
            Representative plans — final pricing is tailored to your call volume and industry.{' '}
            <Link to="/contact" className="font-medium hover:underline" style={{ color: 'rgb(var(--ac-rgb))' }}>Talk to us</Link> for a quote.
          </p>
        </div>
      </section>

      {/* FAQ */}
      <section className="py-20" style={{ background: 'var(--bg-panel)', borderTop: '1px solid var(--bd)' }}>
        <div className={`${CONTAINER} mx-auto max-w-3xl`}>
          <motion.h2 {...reveal} className="mb-10 text-center" style={{ fontSize: '2rem', fontWeight: 900, letterSpacing: '-0.03em', color: 'var(--tx-1)' }}>
            Questions, answered
          </motion.h2>
          <div className="space-y-4">
            {FAQ.map((f, i) => (
              <motion.div key={f.q} {...reveal} transition={{ ...reveal.transition, delay: i * 0.05 }}
                className="rounded-2xl p-6" style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)', boxShadow: 'var(--shadow)' }}>
                <h3 className="mb-1.5 font-bold" style={{ color: 'var(--tx-1)' }}>{f.q}</h3>
                <p className="text-sm" style={{ color: 'var(--tx-2)', lineHeight: 1.7 }}>{f.a}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>
    </div>
  )
}
