import { useCallback, useEffect, useState } from 'react'
import { useAuth } from '../auth/AuthContext'
import {
  API_URL,
  fetchDecisions,
  recordDecision,
  type DecisionRecord,
} from '../data/source'

const ACTIONS: { id: DecisionRecord['action']; label: string; cls: string }[] = [
  { id: 'APPROVED', label: 'Approve', cls: 'v-pass' },
  { id: 'INFO_REQUESTED', label: 'Request more', cls: 'v-watch' },
  { id: 'DECLINED', label: 'Decline', cls: 'v-fail' },
]

/** The human half of the decision.
 *
 *  Every regime in the model card requires human oversight to be recorded, not
 *  merely available, so what an underwriter concluded and why is written to the
 *  API and read back as an audit trail. A snapshot build has nowhere to write
 *  to and says so plainly instead of pretending the control works. */
export default function DecisionPanel({ caseId }: { caseId: string }) {
  const { persona } = useAuth()
  const [trail, setTrail] = useState<DecisionRecord[]>([])
  const [action, setAction] = useState<DecisionRecord['action']>('APPROVED')
  const [rationale, setRationale] = useState('')
  const [status, setStatus] = useState<'idle' | 'saving' | 'saved'>('idle')
  const [error, setError] = useState<string | null>(null)

  const refresh = useCallback(() => {
    if (!API_URL) return
    fetchDecisions(caseId)
      .then(setTrail)
      .catch(() => setTrail([]))
  }, [caseId])

  useEffect(() => {
    setTrail([])
    setRationale('')
    setStatus('idle')
    setError(null)
    refresh()
  }, [caseId, refresh])

  async function submit(e: React.FormEvent) {
    e.preventDefault()
    setStatus('saving')
    setError(null)
    try {
      await recordDecision(caseId, {
        action,
        rationale: rationale.trim(),
        decided_by: persona?.username ?? 'unknown',
      })
      setRationale('')
      setStatus('saved')
      refresh()
    } catch (err) {
      setError(err instanceof Error ? err.message : String(err))
      setStatus('idle')
    }
  }

  const ready = rationale.trim().length >= 5 && Boolean(persona)

  return (
    <section className="decide">
      <div className="panel__head">
        <h2 className="panel__title">Record your decision</h2>
        {trail.length > 0 && (
          <span className="eyebrow">
            {trail.length} entr{trail.length === 1 ? 'y' : 'ies'}
          </span>
        )}
      </div>

      <div className="panel__body">
        {trail.length > 0 && (
          <ol className="decide__trail">
            {trail.map((d, i) => (
              <li key={i} className="decide__entry">
                <span
                  className={`decide__action ${
                    ACTIONS.find((a) => a.id === d.action)?.cls ?? ''
                  }`}
                >
                  {d.action.replace('_', ' ')}
                </span>
                <p className="decide__rationale">{d.rationale}</p>
                <p className="decide__who figure">
                  {d.decided_by} · {d.decided_at}
                </p>
              </li>
            ))}
          </ol>
        )}

        {!API_URL ? (
          <p className="decide__readonly">
            This build is a read-only snapshot, so there is nowhere to write a decision. Start the
            API with <code>uvicorn api:app --app-dir src</code> and rebuild with{' '}
            <code>VITE_API_URL</code> set to record against it.
          </p>
        ) : (
          <form className="decide__form" onSubmit={submit}>
            <div className="decide__actions" role="radiogroup" aria-label="Decision">
              {ACTIONS.map((a) => (
                <button
                  key={a.id}
                  type="button"
                  role="radio"
                  aria-checked={action === a.id}
                  className={`decide__opt ${action === a.id ? `is-on ${a.cls}` : ''}`}
                  onClick={() => setAction(a.id)}
                >
                  {a.label}
                </button>
              ))}
            </div>

            <label className="field">
              <span className="field__label">
                Rationale<span className="field__hint"> at least 5 characters</span>
              </span>
              <textarea
                rows={3}
                value={rationale}
                placeholder="What did you conclude, and on what evidence?"
                onChange={(e) => setRationale(e.target.value)}
              />
            </label>

            <p className="decide__as">
              Recording as <b>{persona?.name}</b>
              <span className="figure"> · @{persona?.username}</span>
            </p>

            <div className="decide__submit">
              <button type="submit" className="btn" disabled={!ready || status === 'saving'}>
                {status === 'saving' ? 'Recording…' : 'Record decision'}
              </button>
              {status === 'saved' && <span className="v-pass decide__ok">Decision recorded.</span>}
              {error && <span className="v-fail decide__ok">{error}</span>}
            </div>
          </form>
        )}
      </div>
    </section>
  )
}
