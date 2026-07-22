/** The six demo personas.
 *
 *  This is a role selector, not authentication — there is no password check and
 *  none is implied. It exists so a decision recorded in the workbench is
 *  attributed to a named person with a seniority, which is what an audit trail
 *  needs. Four underwriting roles (senior/review/analyst desks + oversight
 *  manager), plus an executive who owns the book's financials and an admin who
 *  holds the audit trail. All fictional — no real person's name is a login. */

export type RoleId = 'senior' | 'review' | 'analyst' | 'oversight' | 'executive' | 'admin'

export interface Persona {
  username: string
  name: string
  role: RoleId
  title: string
  /** what this seniority is for, in one line */
  remit: string
}

export const PERSONAS: Persona[] = [
  {
    username: 'mrivera',
    name: 'Maria Rivera',
    role: 'senior',
    title: 'Senior underwriter',
    remit: 'Signs off referred cases and material-misrepresentation declines.',
  },
  {
    username: 'ewong',
    name: 'Evan Wong',
    role: 'review',
    title: 'Underwriter, review desk',
    remit: 'Works the referral queue and requests further evidence.',
  },
  {
    username: 'dpark',
    name: 'Dana Park',
    role: 'analyst',
    title: 'New analyst',
    remit: 'Triages the book; escalates anything outside appetite.',
  },
  {
    username: 'nsethi',
    name: 'Nadia Sethi',
    role: 'oversight',
    title: 'Manager, oversight',
    remit: 'Reviews fairness and the decision trail across the portfolio.',
  },
  {
    username: 'mvale',
    name: 'Marcus Vale',
    role: 'executive',
    title: 'Chief underwriting officer',
    remit: 'Owns risk appetite — the exposure the book takes on and the approve/decline mix.',
  },
  {
    username: 'panand',
    name: 'Priya Anand',
    role: 'admin',
    title: 'Operations administrator',
    remit: 'Receives every recorded decision — the full audit trail.',
  },
]

export const personaByUsername = (u: string) => PERSONAS.find((p) => p.username === u)
