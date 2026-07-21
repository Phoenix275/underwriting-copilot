/** The four demo personas.
 *
 *  This is a role selector, not authentication — there is no password check and
 *  none is implied. It exists so a decision recorded in the workbench is
 *  attributed to a named underwriter with a seniority, which is what an audit
 *  trail needs. All four are fictional demo personas — no real person's name is
 *  used as a login. */

export type RoleId = 'senior' | 'review' | 'analyst' | 'oversight'

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
]

export const personaByUsername = (u: string) => PERSONAS.find((p) => p.username === u)
