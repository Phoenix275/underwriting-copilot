import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { personaByUsername, type Persona } from './roles'

/** Who is signed in. Persisted to localStorage so a reload during a demo does
 *  not drop you back to the sign-in screen. This is presentation-tier only —
 *  the API does not authenticate; the persona's name is passed as the recorded
 *  decision-maker, nothing more. */

const KEY = 'uwc.persona'

interface AuthState {
  persona: Persona | null
  signIn: (username: string) => void
  signOut: () => void
}

const Ctx = createContext<AuthState>({ persona: null, signIn: () => {}, signOut: () => {} })

export const useAuth = () => useContext(Ctx)

export function AuthProvider({ children }: { children: ReactNode }) {
  const [persona, setPersona] = useState<Persona | null>(() => {
    try {
      const saved = localStorage.getItem(KEY)
      return saved ? (personaByUsername(saved) ?? null) : null
    } catch {
      return null
    }
  })

  const signIn = useCallback((username: string) => {
    const p = personaByUsername(username)
    if (!p) return
    setPersona(p)
    try {
      localStorage.setItem(KEY, username)
    } catch {
      /* private mode — sign-in still works for this session */
    }
  }, [])

  const signOut = useCallback(() => {
    setPersona(null)
    try {
      localStorage.removeItem(KEY)
    } catch {
      /* ignore */
    }
  }, [])

  // if the tab is duplicated or another tab signs out, follow it
  useEffect(() => {
    const onStorage = (e: StorageEvent) => {
      if (e.key === KEY) setPersona(e.newValue ? (personaByUsername(e.newValue) ?? null) : null)
    }
    window.addEventListener('storage', onStorage)
    return () => window.removeEventListener('storage', onStorage)
  }, [])

  return <Ctx.Provider value={{ persona, signIn, signOut }}>{children}</Ctx.Provider>
}
