import { useEffect, useRef, useState } from 'react'
import { Link, useNavigate } from 'react-router-dom'
import { AnimatePresence, motion, useInView } from 'framer-motion'
import {
  ArrowRight, BadgeCheck, CalendarCheck, Check, Clock, PhoneCall, PhoneIncoming,
  Scissors, ShieldAlert, Sparkles, Stethoscope, UserRound, Utensils, Wrench,
} from 'lucide-react'
import { api } from '../../api/client'
import type { Category } from '../../api/types'
import { fadeUp, reveal, stagger } from '../../lib/motion'

const CONTAINER = 'w-full px-[clamp(1.25rem,4vw,3.5rem)]'
const delay = (ms: number) => new Promise((r) => setTimeout(r, ms))

const CATEGORY_ICON: Record<string, typeof Stethoscope> = {
  dental_medical: Stethoscope,
  salon_spa: Scissors,
  restaurant: Utensils,
  home_services: Wrench,
}

/* ─── Rotating hero word ─────────────────────────────────────── */
const WORDS = ['call', 'booking', 'patient', 'lead', 'reservation']
function RotatingWord() {
  const [i, setI] = useState(0)
  useEffect(() => {
    const t = setInterval(() => setI((n) => (n + 1) % WORDS.length), 2200)
    return () => clearInterval(t)
  }, [])
  return (
    <span className="relative inline-block" style={{ minWidth: '4ch' }}>
      <AnimatePresence mode="wait">
        <motion.span
          key={i}
          initial={{ y: 22, opacity: 0 }}
          animate={{ y: 0, opacity: 1 }}
          exit={{ y: -18, opacity: 0 }}
          transition={{ duration: 0.4, ease: [0.22, 1, 0.36, 1] }}
          className="inline-block gradient-text"
        >
          {WORDS[i]}
        </motion.span>
      </AnimatePresence>
    </span>
  )
}

/* ─── Animated live-call demo ────────────────────────────────── */
type Phase = 'ringing' | 'greeting' | 'caller' | 'booking' | 'confirmed'
function CallDemo() {
  const [phase, setPhase] = useState<Phase>('ringing')
  useEffect(() => {
    let dead = false
    const run = async () => {
      while (!dead) {
        setPhase('ringing'); await delay(1600)
        setPhase('greeting'); await delay(1900)
        setPhase('caller'); await delay(1700)
        setPhase('booking'); await delay(1600)
        setPhase('confirmed'); await delay(3400)
      }
    }
    run()
    return () => { dead = true }
  }, [])

  const showGreeting = phase !== 'ringing'
  const showCaller = ['caller', 'booking', 'confirmed'].includes(phase)
  const showBooking = ['booking', 'confirmed'].includes(phase)
  const showConfirmed = phase === 'confirmed'

  return (
    <motion.div
      initial={{ opacity: 0, y: 20, scale: 0.97 }}
      animate={{ opacity: 1, y: 0, scale: 1 }}
      transition={{ duration: 0.7, delay: 0.3, ease: [0.22, 1, 0.36, 1] }}
      className="mx-auto w-full max-w-md overflow-hidden rounded-2xl"
      style={{ border: '1px solid var(--bd)', boxShadow: '0 32px 80px rgba(0,0,0,.22)', background: 'var(--bg-card)' }}
    >
      {/* window bar */}
      <div className="flex items-center gap-2 px-4 py-3" style={{ background: 'var(--bg-panel)', borderBottom: '1px solid var(--bd)' }}>
        <span className="h-3 w-3 rounded-full" style={{ background: '#FF5F57' }} />
        <span className="h-3 w-3 rounded-full" style={{ background: '#FFBD2E' }} />
        <span className="h-3 w-3 rounded-full" style={{ background: '#28CA41' }} />
        <div className="ml-3 flex items-center gap-1.5">
          <span className="h-1.5 w-1.5 rounded-full" style={{ background: 'var(--success)' }} />
          <span className="text-xs font-semibold" style={{ color: 'var(--tx-3)' }}>Ava · dental line · live</span>
        </div>
      </div>

      <div className="space-y-3 p-4" style={{ minHeight: 300, background: 'var(--bg-main)' }}>
        <AnimatePresence>
          {phase === 'ringing' && (
            <motion.div key="ring" initial={{ opacity: 0 }} animate={{ opacity: 1 }} exit={{ opacity: 0 }}
              className="flex flex-col items-center justify-center gap-3 py-14">
              <div className="relative flex items-center justify-center">
                <span className="pulse-ring absolute h-14 w-14 rounded-full" style={{ background: 'rgba(var(--ac-rgb),.3)' }} />
                <span className="relative flex h-14 w-14 items-center justify-center rounded-full text-white"
                  style={{ background: 'linear-gradient(135deg, rgb(var(--ac-rgb)), var(--ac-end))' }}>
                  <PhoneIncoming className="h-6 w-6" />
                </span>
              </div>
              <p className="text-sm font-semibold" style={{ color: 'var(--tx-2)' }}>Incoming call…</p>
            </motion.div>
          )}
        </AnimatePresence>

        {showGreeting && (
          <Bubble side="agent">Thanks for calling Bright Smile Dental — this is Ava. How can I help?</Bubble>
        )}
        {showCaller && (
          <Bubble side="caller">Hi, I'd like to book a cleaning for next Tuesday morning.</Bubble>
        )}
        {showBooking && (
          <Bubble side="agent">
            Tuesday works — I have <b>10:30 AM</b> open for a cleaning. Shall I book it?
          </Bubble>
        )}
        {showConfirmed && (
          <motion.div initial={{ opacity: 0, y: 10 }} animate={{ opacity: 1, y: 0 }}
            className="rounded-xl p-3" style={{ background: 'rgba(16,185,129,.10)', border: '1px solid rgba(16,185,129,.25)' }}>
            <div className="flex items-center gap-2 text-sm font-semibold" style={{ color: 'var(--success)' }}>
              <CalendarCheck className="h-4 w-4" /> Appointment booked
            </div>
            <p className="mt-1 text-xs" style={{ color: 'var(--tx-2)' }}>
              Cleaning · Tue 10:30 AM · Ref <b>BSD-4821</b> · confirmation texted
            </p>
          </motion.div>
        )}
      </div>
    </motion.div>
  )
}

function Bubble({ side, children }: { side: 'agent' | 'caller'; children: React.ReactNode }) {
  const isAgent = side === 'agent'
  return (
    <motion.div
      initial={{ opacity: 0, y: 10 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.35 }}
      className={`flex items-end gap-2 ${isAgent ? '' : 'flex-row-reverse'}`}
    >
      <span className="flex h-7 w-7 shrink-0 items-center justify-center rounded-full"
        style={isAgent
          ? { background: 'linear-gradient(135deg, rgb(var(--ac-rgb)), var(--ac-end))', color: '#fff' }
          : { background: 'var(--bg-raised)', border: '1px solid var(--bd)', color: 'var(--tx-2)' }}>
        {isAgent ? <PhoneCall className="h-3.5 w-3.5" /> : <UserRound className="h-3.5 w-3.5" />}
      </span>
      <span className="max-w-[78%] rounded-2xl px-3 py-2 text-sm"
        style={isAgent
          ? { background: 'rgba(var(--ac-rgb),.14)', color: 'var(--tx-1)', border: '1px solid rgba(var(--ac-rgb),.22)' }
          : { background: 'var(--bg-card)', color: 'var(--tx-1)', border: '1px solid var(--bd)' }}>
        {children}
      </span>
    </motion.div>
  )
}

/* ─── Animated counter ───────────────────────────────────────── */
function Counter({ to, prefix = '', suffix = '' }: { to: number; prefix?: string; suffix?: string }) {
  const ref = useRef<HTMLSpanElement>(null)
  const inView = useInView(ref, { once: true })
  const [val, setVal] = useState(0)
  useEffect(() => {
    if (!inView) return
    let cur = 0
    const step = to / 45
    const t = setInterval(() => {
      cur += step
      if (cur >= to) { setVal(to); clearInterval(t) } else setVal(Math.floor(cur))
    }, 18)
    return () => clearInterval(t)
  }, [inView, to])
  return <span ref={ref}>{prefix}{val.toLocaleString()}{suffix}</span>
}

const STATS = [
  { prefix: '', to: 24, suffix: '/7', label: 'Always answering', sub: 'Nights, weekends, holidays' },
  { prefix: '', to: 4, suffix: '', label: 'Industry verticals', sub: 'Purpose-built templates' },
  { prefix: '', to: 0, suffix: '', label: 'Missed calls', sub: 'Every call picked up' },
  { prefix: '<', to: 5, suffix: ' min', label: 'To go live', sub: 'From signup to first call' },
]

const STEPS = [
  {
    num: '01', icon: Sparkles,
    title: 'Pick your industry',
    body: 'Choose dental & medical, salon & spa, restaurant, or home services. Each ships with a tuned persona, the right vocabulary, and the urgent-branch logic that matters for that business.',
  },
  {
    num: '02', icon: PhoneCall,
    title: 'We provision your agent',
    body: 'Your hours, services, and details are compiled into a live conversation flow and a real voice agent — no scripting, no dashboard wrangling. One command, or one click in the console.',
  },
  {
    num: '03', icon: BadgeCheck,
    title: 'Attach a number & go live',
    body: 'Point a phone number at your agent and it starts answering immediately — checking availability against your real hours and booking straight into your system.',
  },
]

const CAPABILITIES = [
  { icon: PhoneCall, title: 'Answers every call', body: 'Picks up on the first ring, 24/7 — no hold music, no voicemail, no missed business.' },
  { icon: ShieldAlert, title: 'Triages the urgent ones', body: 'Recognises emergencies and urgent jobs, and routes them the way your business needs.' },
  { icon: Clock, title: 'Knows your hours', body: 'Checks availability against your real working hours before offering a slot.' },
  { icon: CalendarCheck, title: 'Books appointments', body: 'Captures the details, confirms, and records the booking with a reference number.' },
  { icon: UserRound, title: 'Transfers to a human', body: 'Hands off to a real person the moment a caller asks — never a dead end.' },
  { icon: Sparkles, title: 'Sounds like your brand', body: 'A named persona per industry, speaking your services and your tone.' },
]

/* ─── Page ───────────────────────────────────────────────────── */
export function Home() {
  const navigate = useNavigate()
  const [categories, setCategories] = useState<Category[] | null>(null)

  useEffect(() => {
    api.getCategories().then(setCategories).catch(() => setCategories([]))
  }, [])

  return (
    <div style={{ background: 'var(--bg-main)', color: 'var(--tx-1)' }}>
      {/* ── HERO ─────────────────────────────────────────────── */}
      <section className="bg-hero relative overflow-hidden">
        <div className="pointer-events-none absolute inset-0 overflow-hidden">
          <div className="blob absolute rounded-full opacity-[.07]"
            style={{ width: 640, height: 640, top: '-12%', left: '-6%', background: 'radial-gradient(circle, rgb(var(--ac-rgb)), transparent 70%)' }} />
          <div className="blob-alt absolute rounded-full opacity-[.06]"
            style={{ width: 560, height: 560, bottom: '-16%', right: '-8%', background: 'radial-gradient(circle, #06B6D4, transparent 70%)' }} />
        </div>

        <div className={`${CONTAINER} relative grid grid-cols-1 items-center gap-14 py-20 lg:grid-cols-2 lg:py-24`}>
          <motion.div variants={stagger} initial="initial" animate="animate">
            <motion.div variants={fadeUp}
              className="mb-7 inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-sm font-semibold"
              style={{ background: 'rgba(var(--ac-rgb),.10)', border: '1px solid rgba(var(--ac-rgb),.25)', color: 'rgb(var(--ac-rgb))' }}>
              <Sparkles className="h-3.5 w-3.5" /> RetellAI voice · 4 verticals live
            </motion.div>

            <motion.h1 variants={fadeUp}
              style={{ fontSize: 'clamp(2.4rem,5vw,3.7rem)', fontWeight: 900, lineHeight: 1.08, letterSpacing: '-0.04em', color: 'var(--tx-1)' }}>
              <span className="block">Never miss</span>
              <span className="block">another <RotatingWord />.</span>
            </motion.h1>

            <motion.p variants={fadeUp}
              className="mt-6 max-w-[32rem] text-[1.12rem] leading-relaxed" style={{ color: 'var(--tx-2)' }}>
              QuensultingAI is a voice receptionist that answers your phone around the clock —
              handling FAQs, triaging urgent requests, checking availability, and booking
              appointments. One AI, tuned to your industry.
            </motion.p>

            <motion.div variants={fadeUp} className="mt-9 flex flex-wrap gap-3">
              <button onClick={() => navigate('/contact')} className="btn-primary inline-flex items-center gap-2 rounded-xl px-7 py-3 text-base">
                Get started <ArrowRight className="h-4 w-4" />
              </button>
              <Link to="/about" className="btn-ghost inline-flex items-center gap-2 rounded-xl px-6 py-3 text-base">
                How it works
              </Link>
            </motion.div>

            <motion.div variants={fadeUp} className="mt-8 flex flex-wrap gap-x-5 gap-y-2">
              {['Answers 24/7', 'Books directly', 'Transfers to a human', 'Live in minutes'].map((t) => (
                <span key={t} className="flex items-center gap-1.5 text-sm" style={{ color: 'var(--tx-3)' }}>
                  <Check className="h-3.5 w-3.5" style={{ color: 'var(--success)' }} /> {t}
                </span>
              ))}
            </motion.div>
          </motion.div>

          <div className="relative">
            <div className="bob absolute -left-5 -top-4 z-10 hidden items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold lg:flex"
              style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)', boxShadow: 'var(--shadow-modal)', color: 'var(--tx-1)' }}>
              <span className="h-2 w-2 rounded-full" style={{ background: 'var(--success)' }} /> Picked up on ring 1
            </div>
            <div className="bob-slow absolute -bottom-4 -right-4 z-10 hidden items-center gap-2 rounded-xl px-3 py-2 text-xs font-semibold lg:flex"
              style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)', boxShadow: 'var(--shadow-modal)', color: 'var(--tx-1)' }}>
              <CalendarCheck className="h-3.5 w-3.5" style={{ color: 'rgb(var(--ac-rgb))' }} /> Booked, no human
            </div>
            <CallDemo />
          </div>
        </div>
      </section>

      {/* ── CATEGORY STRIP ───────────────────────────────────── */}
      <div style={{ borderTop: '1px solid var(--bd)', borderBottom: '1px solid var(--bd)', background: 'var(--bg-panel)', overflow: 'hidden' }}>
        <div className={`${CONTAINER} flex items-center gap-6 py-4`}>
          <span className="shrink-0 whitespace-nowrap text-xs font-bold uppercase tracking-widest" style={{ color: 'var(--tx-3)' }}>
            Purpose-built for
          </span>
          <div className="flex-1 overflow-hidden">
            <div className="logo-strip gap-3">
              {[...Array(2)].flatMap((_, dup) =>
                (categories ?? []).map((c) => {
                  const Icon = CATEGORY_ICON[c.key] ?? PhoneCall
                  return (
                    <span key={`${dup}-${c.key}`}
                      className="mx-1.5 flex shrink-0 items-center gap-2 rounded-full px-5 py-2.5 text-sm font-semibold"
                      style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)', color: 'var(--tx-2)' }}>
                      <Icon className="h-4 w-4" style={{ color: 'rgb(var(--ac-rgb))' }} />
                      {c.display_name}
                    </span>
                  )
                })
              )}
            </div>
          </div>
        </div>
      </div>

      {/* ── STATS ────────────────────────────────────────────── */}
      <section className="py-16" style={{ borderBottom: '1px solid var(--bd)' }}>
        <div className={`${CONTAINER} grid grid-cols-2 gap-6 md:grid-cols-4`}>
          {STATS.map((s, i) => (
            <motion.div key={s.label} {...reveal} transition={{ ...reveal.transition, delay: i * 0.08 }} className="text-center">
              <p className="font-black" style={{ fontSize: '2.8rem', lineHeight: 1, letterSpacing: '-0.04em', color: 'rgb(var(--ac-rgb))' }}>
                <Counter to={s.to} prefix={s.prefix} suffix={s.suffix} />
              </p>
              <p className="mt-2 font-bold" style={{ color: 'var(--tx-1)' }}>{s.label}</p>
              <p className="mt-0.5 text-sm" style={{ color: 'var(--tx-3)' }}>{s.sub}</p>
            </motion.div>
          ))}
        </div>
      </section>

      {/* ── HOW IT WORKS ─────────────────────────────────────── */}
      <section className="py-24">
        <div className={CONTAINER}>
          <motion.div {...reveal} className="mb-14 text-center">
            <p className="mb-3 text-sm font-bold uppercase tracking-widest" style={{ color: 'rgb(var(--ac-rgb))' }}>How it works</p>
            <h2 style={{ fontSize: '2.3rem', fontWeight: 900, letterSpacing: '-0.03em', color: 'var(--tx-1)' }}>
              From signup to first booked call in three steps
            </h2>
          </motion.div>

          <div className="space-y-5">
            {STEPS.map((s, i) => (
              <motion.div key={s.num} {...reveal} transition={{ ...reveal.transition, delay: i * 0.08 }}
                className="grid grid-cols-1 items-center gap-6 rounded-2xl p-6 md:grid-cols-[auto_1fr]"
                style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)', boxShadow: 'var(--shadow)' }}>
                <div className="flex items-center gap-4">
                  <span className="flex h-14 w-14 items-center justify-center rounded-2xl text-xl font-black text-white"
                    style={{ background: 'linear-gradient(135deg, rgb(var(--ac-rgb)), var(--ac-end))', boxShadow: '0 8px 24px rgba(var(--ac-rgb),.35)' }}>
                    {s.num}
                  </span>
                  <s.icon className="h-6 w-6 md:hidden" style={{ color: 'rgb(var(--ac-rgb))' }} />
                </div>
                <div>
                  <h3 className="mb-1.5" style={{ fontSize: '1.35rem', fontWeight: 800, letterSpacing: '-0.02em', color: 'var(--tx-1)' }}>{s.title}</h3>
                  <p className="max-w-3xl" style={{ fontSize: '1rem', color: 'var(--tx-2)', lineHeight: 1.7 }}>{s.body}</p>
                </div>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CATEGORY GRID (live) ─────────────────────────────── */}
      <section className="py-24" style={{ background: 'var(--bg-panel)', borderTop: '1px solid var(--bd)', borderBottom: '1px solid var(--bd)' }}>
        <div className={CONTAINER}>
          <motion.div {...reveal} className="mb-14 text-center">
            <p className="mb-3 text-sm font-bold uppercase tracking-widest" style={{ color: 'rgb(var(--ac-rgb))' }}>Ready today</p>
            <h2 style={{ fontSize: '2.3rem', fontWeight: 900, letterSpacing: '-0.03em', color: 'var(--tx-1)' }}>Four verticals, one shared engine</h2>
            <p className="mt-3 text-[1.05rem]" style={{ color: 'var(--tx-2)' }}>Each template is tuned for its industry — persona, vocabulary, and urgent-branch logic.</p>
          </motion.div>

          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-4">
            {(categories ?? []).map((cat, i) => {
              const Icon = CATEGORY_ICON[cat.key] ?? PhoneCall
              return (
                <motion.div key={cat.key} {...reveal} transition={{ ...reveal.transition, delay: i * 0.07 }}
                  className="flex flex-col rounded-2xl p-6"
                  style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)', boxShadow: 'var(--shadow)' }}>
                  <span className="mb-4 flex h-11 w-11 items-center justify-center rounded-xl"
                    style={{ background: 'rgba(var(--ac-rgb),.10)', border: '1px solid rgba(var(--ac-rgb),.22)' }}>
                    <Icon className="h-5 w-5" style={{ color: 'rgb(var(--ac-rgb))' }} />
                  </span>
                  <h3 className="font-bold" style={{ color: 'var(--tx-1)' }}>{cat.display_name}</h3>
                  <p className="mt-1.5 text-sm" style={{ color: 'var(--tx-2)', lineHeight: 1.65 }}>
                    “{cat.agent_persona_name}” handles {cat.booking_noun}s and {cat.customer_noun} inquiries around the clock.
                  </p>
                  {cat.default_services.length > 0 && (
                    <ul className="mt-4 space-y-1.5 border-t pt-4 text-xs" style={{ color: 'var(--tx-3)', borderColor: 'var(--bd)' }}>
                      {cat.default_services.slice(0, 3).map((s) => (
                        <li key={s.name} className="flex items-center gap-1.5">
                          <Check className="h-3 w-3" style={{ color: 'var(--success)' }} /> {s.name}
                        </li>
                      ))}
                    </ul>
                  )}
                </motion.div>
              )
            })}
            {!categories && (
              <p className="col-span-full text-center text-sm" style={{ color: 'var(--tx-3)' }}>Loading categories…</p>
            )}
          </div>
        </div>
      </section>

      {/* ── CAPABILITIES ─────────────────────────────────────── */}
      <section className="py-24">
        <div className={CONTAINER}>
          <motion.div {...reveal} className="mb-14 text-center">
            <p className="mb-3 text-sm font-bold uppercase tracking-widest" style={{ color: 'rgb(var(--ac-rgb))' }}>What it does on every call</p>
            <h2 style={{ fontSize: '2.3rem', fontWeight: 900, letterSpacing: '-0.03em', color: 'var(--tx-1)' }}>A full front desk, on the phone</h2>
          </motion.div>
          <div className="grid grid-cols-1 gap-5 sm:grid-cols-2 lg:grid-cols-3">
            {CAPABILITIES.map((c, i) => (
              <motion.div key={c.title} {...reveal} transition={{ ...reveal.transition, delay: i * 0.06 }}
                className="rounded-2xl p-6" style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)', boxShadow: 'var(--shadow)' }}>
                <span className="mb-4 flex h-10 w-10 items-center justify-center rounded-xl"
                  style={{ background: 'rgba(var(--ac-rgb),.10)', border: '1px solid rgba(var(--ac-rgb),.2)' }}>
                  <c.icon className="h-5 w-5" style={{ color: 'rgb(var(--ac-rgb))' }} />
                </span>
                <h3 className="mb-1.5 font-bold" style={{ color: 'var(--tx-1)' }}>{c.title}</h3>
                <p className="text-sm" style={{ color: 'var(--tx-2)', lineHeight: 1.7 }}>{c.body}</p>
              </motion.div>
            ))}
          </div>
        </div>
      </section>

      {/* ── CTA ──────────────────────────────────────────────── */}
      <section className="relative overflow-hidden py-24" style={{ background: 'var(--bg-panel)', borderTop: '1px solid var(--bd)' }}>
        <div className="pointer-events-none absolute inset-0">
          <div className="blob absolute rounded-full opacity-[.07]"
            style={{ width: 640, height: 640, top: '50%', left: '50%', transform: 'translate(-50%,-50%)', background: 'radial-gradient(circle, rgb(var(--ac-rgb)), transparent 65%)' }} />
        </div>
        <div className={`${CONTAINER} relative`}>
          <motion.div {...reveal} className="mx-auto max-w-2xl text-center">
            <span className="mx-auto mb-8 flex h-20 w-20 items-center justify-center rounded-3xl text-white"
              style={{ background: 'linear-gradient(135deg, rgb(var(--ac-rgb)), var(--ac-end))', boxShadow: '0 20px 60px rgba(var(--ac-rgb),.4)' }}>
              <PhoneCall className="h-9 w-9" />
            </span>
            <h2 style={{ fontSize: '2.6rem', fontWeight: 900, letterSpacing: '-0.04em', color: 'var(--tx-1)' }}>Ready to stop missing calls?</h2>
            <p className="mx-auto mt-4 max-w-lg text-[1.1rem]" style={{ color: 'var(--tx-2)', lineHeight: 1.7 }}>
              Tell us about your business and we’ll stand up your AI receptionist — usually within minutes.
            </p>
            <div className="mt-9 flex flex-wrap justify-center gap-4">
              <button onClick={() => navigate('/contact')} className="btn-primary inline-flex items-center gap-2 rounded-xl px-9 py-4 text-base">
                Get started <ArrowRight className="h-5 w-5" />
              </button>
              <Link to="/portal" className="btn-ghost inline-flex items-center gap-2 rounded-xl px-7 py-4 text-base">
                Client login
              </Link>
            </div>
          </motion.div>
        </div>
      </section>
    </div>
  )
}
