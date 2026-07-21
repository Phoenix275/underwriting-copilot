import type { Case, Desk } from '../data/types'
import type { RoleId } from '../auth/roles'

/** Desk presentation and the mapping from a signed-in role to a desk.
 *
 *  Three of the four personas own a desk and see the referrals routed to them by
 *  difficulty; the manager (oversight) owns none and sees the whole queue plus
 *  the routing overview. This is the "different depending on who logs in" the
 *  workbench is built around. */

export const DESK_LABEL: Record<Desk, string> = {
  senior: 'Senior underwriter',
  review: 'Review desk',
  analyst: 'New analyst',
}

/** short tag for the queue column */
export const DESK_TAG: Record<Desk, string> = {
  senior: 'Senior',
  review: 'Review',
  analyst: 'Analyst',
}

/** difficulty bands, only for display next to a case */
export function difficultyBand(d: number | null): 'complex' | 'standard' | 'straightforward' | null {
  if (d == null) return null
  return d >= 33 ? 'complex' : d >= 24 ? 'standard' : 'straightforward'
}

/** the desk a signed-in role works; null for the manager, who sees everything */
export function deskForRole(role: RoleId): Desk | null {
  return role === 'oversight' ? null : (role as Desk)
}

/** is this case in the signed-in person's queue?
 *  underwriters: referred cases routed to their desk. manager: every referral. */
export function isMine(c: Case, role: RoleId): boolean {
  if (!c.referred) return false
  const desk = deskForRole(role)
  return desk === null ? true : c.assigned_desk === desk
}
