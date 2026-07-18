import { Link } from 'react-router-dom'
import { motion } from 'framer-motion'
import {
  ArrowRight, GitBranch, Layers, PhoneCall, ServerCog, ShieldCheck, Sparkles, Workflow,
} from 'lucide-react'
import { fadeUp, reveal, stagger } from '../../lib/motion'

const CONTAINER = 'w-full px-[clamp(1.25rem,4vw,3.5rem)]'

const PILLARS = [
  {
    icon: Layers,
    title: 'One engine, many industries',
    body: 'Every receptionist runs on the same proven conversation engine — greetings, FAQs, availability logic, booking, and hand-off to a human are shared and battle-tested. What changes per industry is the vocabulary, the persona, and the one branch that matters most: an emergency for a clinic, an urgent job for a home-services call.',
  },
  {
    icon: GitBranch,
    title: 'Curated templates, not a blank canvas',
    body: 'Rather than a generic bot-builder, we ship tuned templates for dental & medical, salon & spa, restaurant, and home services. Each supplies the persona, working-hours copy, starter services, and the details it should collect — so a new business is live in minutes, tuned for its trade from the very first call.',
  },
  {
    icon: PhoneCall,
    title: 'A phone line, not a chat widget',
    body: 'The agent runs on real telephony. It answers the actual phone, checks availability against your real working hours, books directly into your system, and transfers to a human whenever a caller asks — every call handled, day or night.',
  },
]

const STACK = [
  { icon: PhoneCall, title: 'RetellAI voice', body: 'Natural, low-latency voice conversations over real phone numbers.' },
  { icon: ServerCog, title: 'FastAPI backend', body: 'Multi-tenant Python service that resolves each business, checks hours, and records bookings.' },
  { icon: Workflow, title: 'Template engine', body: 'A shared 14-node flow parameterised per business — no hand-authored call scripts.' },
  { icon: ShieldCheck, title: 'Per-tenant isolation', body: 'Every business has its own agent, its own webhook token, and its own data.' },
]

export function About() {
  return (
    <div style={{ background: 'var(--bg-main)', color: 'var(--tx-1)' }}>
      {/* ── HERO ─────────────────────────────────────────────── */}
      <section className="bg-hero relative overflow-hidden" style={{ borderBottom: '1px solid var(--bd)' }}>
        <div className={`${CONTAINER} relative py-24 text-center`}>
          <motion.div variants={stagger} initial="initial" animate="animate">
            <motion.div variants={fadeUp}
              className="mb-6 inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-sm font-semibold"
              style={{ background: 'rgba(var(--ac-rgb),.10)', border: '1px solid rgba(var(--ac-rgb),.25)', color: 'rgb(var(--ac-rgb))' }}>
              <Sparkles className="h-3.5 w-3.5" /> About QuensultingAI
            </motion.div>
            <motion.h1 variants={fadeUp}
              style={{ fontSize: 'clamp(2.4rem,5vw,3.4rem)', fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1.1, color: 'var(--tx-1)' }}>
              Missed calls are<br /><span className="gradient-text">missed business.</span>
            </motion.h1>
            <motion.p variants={fadeUp}
              className="mx-auto mt-6 max-w-2xl text-[1.15rem]" style={{ color: 'var(--tx-2)', lineHeight: 1.75 }}>
              Most small and medium businesses can’t staff a phone line around the clock — so calls
              go unanswered and bookings slip away. We built QuensultingAI to close that gap with a
              voice receptionist that never sleeps. Here’s how it works, in plain terms.
            </motion.p>
          </motion.div>
        </div>
      </section>

      {/* ── MISSION ──────────────────────────────────────────── */}
      <section className="py-24" style={{ background: 'var(--bg-panel)', borderBottom: '1px solid var(--bd)' }}>
        <div className={CONTAINER}>
          <motion.div {...reveal}>
            <p className="mb-4 text-sm font-bold uppercase tracking-widest" style={{ color: 'rgb(var(--ac-rgb))' }}>Our mission</p>
            <blockquote className="max-w-3xl" style={{ fontSize: '1.7rem', fontWeight: 800, lineHeight: 1.45, letterSpacing: '-0.02em', color: 'var(--tx-1)' }}>
              “Answering the phone shouldn’t require hiring a front desk. Every business deserves a
              receptionist that picks up on the first ring — at 2 PM or 2 AM.”
            </blockquote>
            <p className="mt-6 max-w-2xl" style={{ fontSize: '1.05rem', color: 'var(--tx-2)', lineHeight: 1.75 }}>
              We started with one live-tested dental receptionist and turned it into a reusable
              platform: the same proven pipeline, now standing up receptionists for any industry
              from a single command — or a single click.
            </p>
          </motion.div>
        </div>
      </section>

      {/* ── PILLARS ──────────────────────────────────────────── */}
      <section className="py-24">
        <div className={CONTAINER}>
          <motion.div {...reveal} className="mb-14 text-center">
            <p className="mb-3 text-sm font-bold uppercase tracking-widest" style={{ color: 'rgb(var(--ac-rgb))' }}>The approach</p>
            <h2 style={{ fontSize: '2.3rem', fontWeight: 900, letterSpacing: '-0.03em', color: 'var(--tx-1)' }}>What makes it work</h2>
          </motion.div>
          <div className="space-y-5">
            {PILLARS.map((p, i) => (
              <motion.div key={p.title} {...reveal} transition={{ ...reveal.transition, delay: i * 0.08 }}
                className="grid grid-cols-1 gap-5 rounded-2xl p-7 md:grid-cols-[auto_1fr]"
                style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)', boxShadow: 'var(--shadow)' }}>
                <span className="flex h-12 w-12 items-center justify-center rounded-xl"
                  style={{ background: 'rgba(var(--ac-rgb),.10)', border: '1px solid rgba(var(--ac-rgb),.2)' }}>
                  <p.icon className="h-6 w-6" style={{ color: 'rgb(var(--ac-rgb))' }} />
                </span>
                <div>
                  <h3 className="mb-1.5" style={{ fontSize: '1.25rem', fontWeight: 800, color: 'var(--tx-1)' }}>{p.title}</h3>
                  <p style={{ fontSize: '1rem', color: 'var(--tx-2)', lineHeight: 1.75 }}>{p.body}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── STACK ────────────────────────────────────────────── */}
      <section className="py-24" style={{ background: 'var(--bg-panel)', borderTop: '1px solid var(--bd)', borderBottom: '1px solid var(--bd)' }}>
        <div className={CONTAINER}>
          <motion.div {...reveal} className="mb-14 text-center">
            <p className="mb-3 text-sm font-bold uppercase tracking-widest" style={{ color: 'rgb(var(--ac-rgb))' }}>Under the hood</p>
            <h2 style={{ fontSize: '2.3rem', fontWeight: 900, letterSpacing: '-0.03em', color: 'var(--tx-1)' }}>Built on a proven stack</h2>
          </motion.div>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {STACK.map((s, i) => (
              <motion.div key={s.title} {...reveal} transition={{ ...reveal.transition, delay: i * 0.07 }}
                className="rounded-2xl p-6" style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)', boxShadow: 'var(--shadow)' }}>
                <span className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl"
                  style={{ background: 'rgba(var(--ac-rgb),.10)', border: '1px solid rgba(var(--ac-rgb),.2)' }}>
                  <s.icon className="h-5 w-5" style={{ color: 'rgb(var(--ac-rgb))' }} />
                </span>
                <h3 className="mb-1.5 font-bold" style={{ color: 'var(--tx-1)' }}>{s.title}</h3>
                <p className="text-sm" style={{ color: 'var(--tx-2)', lineHeight: 1.7 }}>{s.body}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────── */}
      <section className="py-20">
        <div className={`${CONTAINER} text-center`}>
          <motion.div {...reveal} className="mx-auto max-w-xl">
            <h2 style={{ fontSize: '1.9rem', fontWeight: 900, letterSpacing: '-0.03em', color: 'var(--tx-1)' }}>
              Want to see it on your business?
            </h2>
            <p className="mt-3" style={{ fontSize: '1.05rem', color: 'var(--tx-2)' }}>
              Tell us about your business and we’ll walk you through setup.
            </p>
            <Link to="/contact" className="btn-primary mt-7 inline-flex items-center gap-2 rounded-xl px-7 py-3 text-base">
              Get in touch <ArrowRight className="h-4 w-4" />
            </Link>
          </motion.div>
        </div>
      </section>
    </div>
  )
}
