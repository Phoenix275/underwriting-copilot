import { useAuth } from '../auth/AuthContext'

/** Who you are signed in as, with a way out. Sits above the data-source badge
 *  in the rail so the two pieces of session context are together. */
export default function RoleBadge() {
  const { persona, signOut } = useAuth()
  if (!persona) return null

  return (
    <div className="rolebadge">
      <div className="rolebadge__who">
        <span className="rolebadge__name">{persona.name}</span>
        <span className="rolebadge__role">{persona.title}</span>
      </div>
      <button type="button" className="rolebadge__out" onClick={signOut}>
        Sign out
      </button>
    </div>
  )
}
