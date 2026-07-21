import type { Case } from '../data/types'

/** The plane's horizontal axis: how close a case sits to failing the financial
 *  screen. The affordability verdict itself is only three-valued, which would
 *  stack 200 cases into three columns; this is the continuous distance behind
 *  it — the worst of the four indicators, each expressed as a fraction of its
 *  own fail threshold. 100 means a case is exactly on the line. */
export function strainScore(c: Case): number {
  const a = c.afford
  const netMonthly = (Math.max(c.income, 1) * 0.78) / 12

  const ratios = [
    a.pti / 0.1, // fails above 10% of gross income
    a.cov_mult / (a.cov_cap * 1.1), // fails above 110% of the age-banded cap
    a.dsr / 0.35, // fails above 35% of net income
    // disposable income fails at zero; treat a quarter of net income as clear
    1 - Math.min(Math.max(a.disposable / (0.25 * netMonthly), 0), 1),
  ]
  const worst = Math.max(...ratios)

  // Below the fail line the scale is linear, with the line itself at 80.
  // Above it a case is already referred, but by how far still matters to an
  // underwriter — so the tail is compressed asymptotically rather than clipped,
  // which would stack every failing case in one column on the plane's edge.
  return worst <= 1 ? worst * 80 : 80 + 20 * (1 - Math.exp(-(worst - 1) * 1.1))
}

/** Both plane axes for a case, normalised to 0..1. */
export function planePosition(c: Case): { u: number; v: number } {
  return {
    u: Math.min(strainScore(c), 100) / 100,
    v: Math.min(c.risk_score, 100) / 100,
  }
}

export type PortfolioFilter =
  | 'mine'
  | 'all'
  | 'green'
  | 'yellow'
  | 'red'
  | 'conflicts'
  | 'unaffordable'

// 'mine' is added by the view because it depends on who is signed in
export const FILTERS: { id: PortfolioFilter; label: string }[] = [
  { id: 'all', label: 'All' },
  { id: 'green', label: 'Approve' },
  { id: 'yellow', label: 'Refer' },
  { id: 'red', label: 'Decline' },
  { id: 'conflicts', label: 'Conflicts found' },
  { id: 'unaffordable', label: 'Not justified' },
]

export function matchesFilter(c: Case, f: PortfolioFilter): boolean {
  switch (f) {
    case 'all':
      return true
    case 'conflicts':
      return c.conflicts.length > 0
    case 'unaffordable':
      return c.afford.verdict === 'fail'
    default:
      return c.verdict === f
  }
}
