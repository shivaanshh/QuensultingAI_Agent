import { useEffect, useState, type FormEvent } from 'react'
import { motion } from 'framer-motion'
import { Clock, Mail, PhoneCall, Send, Sparkles } from 'lucide-react'
import { api, ApiError } from '../../api/client'
import type { Category } from '../../api/types'
import { Input, Label, Select, Textarea } from '../../components/ui/Field'
import { Alert } from '../../components/ui/Alert'
import { fadeUp, stagger } from '../../lib/motion'

const CONTAINER = 'w-full px-[clamp(1.25rem,4vw,3.5rem)]'

const HIGHLIGHTS = [
  { icon: PhoneCall, title: 'Answers every call', body: '24/7 coverage — nights, weekends, and holidays included.' },
  { icon: Clock, title: 'Live in minutes', body: 'From a quick chat to a working agent, usually the same day.' },
  { icon: Sparkles, title: 'Tuned to your trade', body: 'A persona and vocabulary built for your industry, not generic.' },
]

export function Contact() {
  const [categories, setCategories] = useState<Category[]>([])
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [businessType, setBusinessType] = useState('')
  const [message, setMessage] = useState('')
  const [submitting, setSubmitting] = useState(false)
  const [result, setResult] = useState<{ tone: 'success' | 'error'; text: string } | null>(null)

  useEffect(() => {
    api.getCategories().then(setCategories).catch(() => setCategories([]))
  }, [])

  async function handleSubmit(e: FormEvent) {
    e.preventDefault()
    setSubmitting(true)
    setResult(null)
    try {
      const res = await api.submitContact({ name, email, business_type: businessType, message })
      setResult({ tone: 'success', text: res.message })
      setName('')
      setEmail('')
      setBusinessType('')
      setMessage('')
    } catch (err) {
      const text = err instanceof ApiError ? err.message : 'Something went wrong. Please try again.'
      setResult({ tone: 'error', text })
    } finally {
      setSubmitting(false)
    }
  }

  return (
    <div className="bg-hero" style={{ color: 'var(--tx-1)' }}>
      <div className={`${CONTAINER} grid grid-cols-1 gap-12 py-20 lg:grid-cols-2`}>
        {/* Left: pitch */}
        <motion.div variants={stagger} initial="initial" animate="animate">
          <motion.div variants={fadeUp}
            className="mb-6 inline-flex items-center gap-2 rounded-full px-3.5 py-1.5 text-sm font-semibold"
            style={{ background: 'rgba(var(--ac-rgb),.10)', border: '1px solid rgba(var(--ac-rgb),.25)', color: 'rgb(var(--ac-rgb))' }}>
            <Mail className="h-3.5 w-3.5" /> Get in touch
          </motion.div>
          <motion.h1 variants={fadeUp}
            style={{ fontSize: 'clamp(2.2rem,4.5vw,3.2rem)', fontWeight: 900, letterSpacing: '-0.04em', lineHeight: 1.1, color: 'var(--tx-1)' }}>
            Let’s set up your <span className="gradient-text">AI receptionist</span>
          </motion.h1>
          <motion.p variants={fadeUp} className="mt-5 max-w-lg text-[1.1rem]" style={{ color: 'var(--tx-2)', lineHeight: 1.7 }}>
            Tell us a bit about your business and we’ll follow up about getting your receptionist
            live — answering calls, triaging the urgent ones, and booking appointments.
          </motion.p>

          <motion.div variants={fadeUp} className="mt-10 space-y-4">
            {HIGHLIGHTS.map((h) => (
              <div key={h.title} className="flex items-start gap-3.5">
                <span className="mt-0.5 flex h-10 w-10 shrink-0 items-center justify-center rounded-xl"
                  style={{ background: 'rgba(var(--ac-rgb),.10)', border: '1px solid rgba(var(--ac-rgb),.2)' }}>
                  <h.icon className="h-5 w-5" style={{ color: 'rgb(var(--ac-rgb))' }} />
                </span>
                <div>
                  <p className="font-bold" style={{ color: 'var(--tx-1)' }}>{h.title}</p>
                  <p className="text-sm" style={{ color: 'var(--tx-2)' }}>{h.body}</p>
                </div>
              </div>
            ))}
          </motion.div>
        </motion.div>

        {/* Right: form */}
        <motion.div initial={{ opacity: 0, y: 24 }} animate={{ opacity: 1, y: 0 }} transition={{ duration: 0.55, delay: 0.15 }}
          className="rounded-2xl p-7 lg:p-8"
          style={{ background: 'var(--bg-card)', border: '1px solid var(--bd)', boxShadow: 'var(--shadow-lg)' }}>
          <form onSubmit={handleSubmit} className="space-y-5">
            <div>
              <Label htmlFor="name">Name</Label>
              <Input id="name" required value={name} onChange={(e) => setName(e.target.value)} placeholder="Jane Doe" />
            </div>
            <div>
              <Label htmlFor="email">Email</Label>
              <Input id="email" type="email" required value={email} onChange={(e) => setEmail(e.target.value)} placeholder="you@business.com" />
            </div>
            <div>
              <Label htmlFor="business_type">Business type</Label>
              <Select id="business_type" value={businessType} onChange={(e) => setBusinessType(e.target.value)}>
                <option value="">Select one (optional)</option>
                {categories.map((c) => (
                  <option key={c.key} value={c.key}>{c.display_name}</option>
                ))}
              </Select>
            </div>
            <div>
              <Label htmlFor="message">Message</Label>
              <Textarea id="message" rows={5} required value={message} onChange={(e) => setMessage(e.target.value)}
                placeholder="Tell us about your business and what you'd like your receptionist to handle." />
            </div>

            {result && <Alert tone={result.tone}>{result.text}</Alert>}

            <button type="submit" disabled={submitting}
              className="btn-primary inline-flex w-full items-center justify-center gap-2 rounded-xl px-6 py-3 text-base">
              {submitting ? 'Sending…' : (<><Send className="h-4 w-4" /> Send message</>)}
            </button>
            <p className="text-center text-xs" style={{ color: 'var(--tx-3)' }}>
              We’ll only use your details to follow up about your receptionist.
            </p>
          </form>
        </motion.div>
      </div>
    </div>
  )
}
