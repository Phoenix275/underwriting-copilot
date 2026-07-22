import { useEffect, useMemo, useState } from 'react'
import { motion } from 'motion/react'
import { useData } from '../data/DataContext'
import { useAuth } from '../auth/AuthContext'
import { API_URL, fetchAllDecisions, type DecisionEntry } from '../data/source'
import { usdShort } from '../lib/format'
import '../styles/exec.css'

const ACTION: Record<DecisionEntry['action'], { label: string; tone: string }> = {
  APPROVED: { label: 'Approved', tone: 'pass' },
  INFO_REQUESTED: { label: 'Info requested', tone: 'watch' },
  DECLINED: { label: 'Declined', tone: 'fail' },
}

/** The admin's screen: every decision any underwriter recorded, newest first.
 *  This is the receiving end of the "Record your decision" panel — the audit
 *  trail an operations administrator holds. */
export default function DecisionsAudit({ onOpen }: { onOpen: (id: string) => void }) {
  const { cases } = useData()
  const { persona } = useAuth()
  const [entries, setEntries] = useState<DecisionEntry[] | null>(null)

  useEffect(() => {
    let live = true
    fetchAllDecisions()
      .then((e) => live && setEntries(e))
      .catch(() => live && setEntries([]))
    return () => {
      live = false
    }
  }, [])

  const caseById = useMemo(() => new Map(cases.map((c) => [c.id, c])), [cases])
  const counts = useMemo(() => {
    const c = { APPROVED: 0, INFO_REQUESTED: 0, DECLINED: 0 }
    for (const e of entries ?? []) c[e.action] += 1
    return c
  }, [entries])

  return (
    <>
      <div className="viewhead">
        <p className="eyebrow">Admin · audit trail</p>
        <h1 className="viewhead__title">Recorded decisions</h1>
        <p className="viewhead__lede">
          {persona?.name} — {persona?.title.toLowerCase()}. Every decision an underwriter records
          lands here, attributed and time-stamped.{' '}
          {API_URL
            ? 'Read from the shared audit trail.'
            : 'This build has no server, so the trail is the decisions recorded in this browser.'}
        </p>
      </div>

      <div className="viewbody">
        {entries && entries.length > 0 && (
          <div className="stats stats--fin auditcounts">
            <div className="fintile"><span className="fintile__label">Recorded</span>
              <span className="fintile__value figure">{entries.length}</span>
              <span className="fintile__sub">total decisions</span></div>
            <div className="fintile"><span className="fintile__label v-pass">Approved</span>
              <span className="fintile__value figure v-pass">{counts.APPROVED}</span>
              <span className="fintile__sub">signed off</span></div>
            <div className="fintile"><span className="fintile__label v-watch">Info requested</span>
              <span className="fintile__value figure v-watch">{counts.INFO_REQUESTED}</span>
              <span className="fintile__sub">sent back</span></div>
            <div className="fintile"><span className="fintile__label v-fail">Declined</span>
              <span className="fintile__value figure v-fail">{counts.DECLINED}</span>
              <span className="fintile__sub">turned away</span></div>
          </div>
        )}

        <div className="srule">
          <span className="eyebrow">The trail</span>
        </div>

        {entries === null ? (
          <div className="panel"><div className="panel__body"><p className="sectionlede" style={{ margin: 0 }}>Loading the audit trail…</p></div></div>
        ) : entries.length === 0 ? (
          <div className="panel">
            <div className="panel__body">
              <p className="sectionlede" style={{ margin: 0 }}>
                No decisions recorded yet. Open a case and use <b>Record your decision</b> — every one
                an underwriter records will appear here, with who recorded it and when.
              </p>
            </div>
          </div>
        ) : (
          <ul className="audit">
            {entries.map((e, i) => {
              const c = caseById.get(e.caseId)
              const meta = ACTION[e.action]
              return (
                <motion.li
                  key={`${e.caseId}-${i}`}
                  className="audit__row"
                  initial={{ opacity: 0, y: 6 }}
                  animate={{ opacity: 1, y: 0 }}
                  transition={{ duration: 0.25, delay: Math.min(i * 0.02, 0.3) }}
                >
                  <span className={`audit__action v-${meta.tone}`}>{meta.label}</span>
                  <div className="audit__body">
                    <button type="button" className="audit__case" onClick={() => onOpen(e.caseId)}>
                      {e.caseId}
                      {c && (
                        <span className="audit__casemeta">
                          {' '}· {usdShort(c.coverage)} {c.policy}
                        </span>
                      )}
                    </button>
                    {e.rationale && <p className="audit__rationale">{e.rationale}</p>}
                  </div>
                  <div className="audit__who">
                    <span className="figure">@{e.decided_by}</span>
                    <span className="audit__when figure">{e.decided_at ?? '—'}</span>
                  </div>
                </motion.li>
              )
            })}
          </ul>
        )}
      </div>
    </>
  )
}
