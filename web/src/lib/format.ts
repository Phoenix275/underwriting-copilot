import type { AffordVerdict, Verdict } from '../data/types'

export const usd = (n: number, decimals = 0) =>
  n.toLocaleString('en-US', {
    style: 'currency',
    currency: 'USD',
    minimumFractionDigits: decimals,
    maximumFractionDigits: decimals,
  })

/** Compact money for axis ticks and dense tables: $1.2M, $840k. */
export const usdShort = (n: number) => {
  const abs = Math.abs(n)
  if (abs >= 1e6) return `$${(n / 1e6).toFixed(abs >= 1e7 ? 0 : 1)}M`
  if (abs >= 1e3) return `$${Math.round(n / 1e3)}k`
  return `$${Math.round(n)}`
}

export const pct = (n: number, decimals = 0) => `${(n * 100).toFixed(decimals)}%`

/** Verdict → CSS custom property. Colour is only ever derived through here so
 *  there is exactly one place that decides what a verdict looks like. */
export const verdictVar = (v: Verdict) =>
  v === 'green' ? 'var(--pass)' : v === 'yellow' ? 'var(--watch)' : 'var(--fail)'

export const affordVar = (v: AffordVerdict) =>
  v === 'pass' ? 'var(--pass)' : v === 'strain' ? 'var(--watch)' : 'var(--fail)'

export const verdictClass = (v: Verdict) =>
  v === 'green' ? 'v-pass' : v === 'yellow' ? 'v-watch' : 'v-fail'

export const affordClass = (v: AffordVerdict) =>
  v === 'pass' ? 'v-pass' : v === 'strain' ? 'v-watch' : 'v-fail'

/** Underwriters read "REFER", not "MANUAL REVIEW", on a dense queue row. */
export const shortDecision = (d: string) =>
  d === 'MANUAL REVIEW' ? 'REFER' : d === 'APPROVE' ? 'APPROVE' : 'DECLINE'

export const titleCase = (s: string) =>
  s.replace(/_/g, ' ').replace(/\b\w/g, (m) => m.toUpperCase())
