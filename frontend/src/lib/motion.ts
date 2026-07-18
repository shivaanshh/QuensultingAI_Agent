import type { Variants } from 'framer-motion'

const EASE = [0.22, 1, 0.36, 1] as const

export const fadeUp: Variants = {
  initial: { opacity: 0, y: 28 },
  animate: { opacity: 1, y: 0, transition: { duration: 0.55, ease: EASE } },
}

export const stagger: Variants = {
  animate: { transition: { staggerChildren: 0.09 } },
}

/** Props for a scroll-triggered reveal on any motion element. */
export const reveal = {
  initial: { opacity: 0, y: 24 },
  whileInView: { opacity: 1, y: 0 },
  viewport: { once: true, margin: '-60px' },
  transition: { duration: 0.5, ease: EASE },
}
