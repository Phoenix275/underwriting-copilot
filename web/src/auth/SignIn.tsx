import { useState } from 'react'
import Seal from '../components/Seal'
import { PERSONAS, type RoleId } from './roles'
import { useAuth } from './AuthContext'
import '../styles/signin.css'

const ROLE_SEAL: Record<RoleId, number> = {
  senior: 9,
  review: 7,
  analyst: 5,
  oversight: 11,
  executive: 13,
  admin: 6,
}

export default function SignIn() {
  const { signIn } = useAuth()
  const [picked, setPicked] = useState<string | null>(null)

  return (
    <main className="signin">
      <div className="signin__card">
        <div className="signin__mark">
          <Seal size={44} petals={9} copies={4} />
          <div>
            <div className="signin__word">Underwriting Copilot</div>
            <div className="signin__sub">Financial viability workbench</div>
          </div>
        </div>

        <p className="signin__lede">
          Choose an underwriter to sign in as. Decisions you record are attributed to that name.
        </p>

        <ul className="signin__roles">
          {PERSONAS.map((p) => (
            <li key={p.username}>
              <button
                type="button"
                className={`rolecard${picked === p.username ? ' is-picked' : ''}`}
                aria-pressed={picked === p.username}
                onClick={() => setPicked(p.username)}
                onDoubleClick={() => signIn(p.username)}
              >
                <Seal size={26} petals={ROLE_SEAL[p.role]} copies={4} className="rolecard__seal" />
                <span className="rolecard__name">{p.name}</span>
                <span className="rolecard__title">{p.title}</span>
                <span className="rolecard__remit">{p.remit}</span>
                <span className="rolecard__user figure">{p.username}</span>
              </button>
            </li>
          ))}
        </ul>

        <button
          type="button"
          className="signin__go"
          disabled={!picked}
          onClick={() => picked && signIn(picked)}
        >
          {picked ? `Sign in as ${PERSONAS.find((p) => p.username === picked)!.name}` : 'Select a role'}
        </button>

        <p className="signin__note">
          Demo sign-in — no password, no authentication. Role selection only, so a recorded decision
          carries a name and seniority. Do not treat this as a security boundary.
        </p>
      </div>
    </main>
  )
}
