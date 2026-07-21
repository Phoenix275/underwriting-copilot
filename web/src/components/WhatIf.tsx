import { useMemo, useState } from 'react'
import { motion } from 'motion/react'
import type { Case } from '../data/types'
import { caseToApplication, scoreApplication, type Application } from '../lib/score'
import { affordClass, pct, usd, verdictClass } from '../lib/format'

/** "What if this applicant's circumstances were different?"
 *
 *  A focused sensitivity tool that belongs to one case — you stay on the file
 *  and nudge the handful of levers that actually move an underwriting decision,
 *  watching the verdict re-derive against the case's real recorded outcome. It
 *  is deliberately not the full application form: entering a brand-new applicant
 *  is a separate task on its own screen. */

const LEVERS: {
  key: keyof Application
  label: string
  hint?: string
  step?: number
  min?: number
  max?: number
}[] = [
  { key: 'coverage', label: 'Cover requested', hint: 'USD', step: 25000, min: 25000 },
  { key: 'income', label: 'Annual income', hint: 'USD', step: 5000, min: 0 },
  { key: 'monthlyExpenses', label: 'Monthly expenses', hint: 'USD', step: 100, min: 0 },
  { key: 'debt', label: 'Outstanding debt', hint: 'USD', step: 5000, min: 0 },
  { key: 'age', label: 'Age', step: 1, min: 18, max: 80 },
]

export default function WhatIf({ c }: { c: Case }) {
  const base = useMemo(() => caseToApplication(c), [c])
  const [a, setA] = useState<Application>(base)

  const baseline = useMemo(() => scoreApplication(base), [base])
  const result = useMemo(() => scoreApplication(a), [a])

  const set = <K extends keyof Application>(k: K, v: Application[K]) =>
    setA((prev) => ({ ...prev, [k]: v }))

  const touched = LEVERS.some((l) => a[l.key] !== base[l.key]) || a.smoker !== base.smoker
  const verdictChanged = result.verdict !== baseline.verdict

  return (
    <section className="panel whatif">
      <div className="panel__head">
        <h2 className="panel__title">What if?</h2>
        <span className="eyebrow">Sensitivity on this applicant</span>
      </div>

      <div className="panel__body whatif__body">
        <div className="whatif__controls">
          <p className="whatif__lede">
            Adjust {c.name}&rsquo;s circumstances and the verdict re-derives against their real
            outcome. This stays on the case — to score a brand-new applicant, use New application.
          </p>

          {LEVERS.map((l) => (
            <label key={String(l.key)} className="whatif__lever">
              <span className="whatif__leverlabel">
                {l.label}
                {l.hint && <span className="whatif__leverhint"> {l.hint}</span>}
              </span>
              <input
                type="number"
                step={l.step}
                min={l.min}
                max={l.max}
                value={Math.round(a[l.key] as number)}
                onChange={(e) => set(l.key, (Number(e.target.value) || 0) as Application[typeof l.key])}
              />
            </label>
          ))}

          <label className="whatif__lever">
            <span className="whatif__leverlabel">Tobacco</span>
            <select
              value={a.smoker}
              onChange={(e) => set('smoker', e.target.value as Application['smoker'])}
            >
              <option>Non-smoker</option>
              <option>Former smoker</option>
              <option>Smoker</option>
            </select>
          </label>

          {touched && (
            <button type="button" className="btn btn--ghost whatif__reset" onClick={() => setA(base)}>
              Reset to the real application
            </button>
          )}
        </div>

        <div className="whatif__out" aria-live="polite">
          <div className={`whatif__verdict ${verdictClass(result.verdict)}`}>
            <span className="whatif__decision">{result.decision}</span>
            <span className="whatif__rate">{result.rate_class}</span>
            {verdictChanged && (
              <motion.span
                key={result.verdict}
                className="whatif__delta"
                initial={{ opacity: 0, y: -4 }}
                animate={{ opacity: 1, y: 0 }}
              >
                changed from {baseline.decision}
              </motion.span>
            )}
          </div>

          <dl className="whatif__figures">
            <Delta label="Composite risk" now={result.risk_score} was={baseline.risk_score} />
            <Delta
              label="Affordability"
              hide
              text={result.afford.label}
              cls={affordClass(result.afford.verdict)}
              wasText={baseline.afford.label}
              changed={result.afford.verdict !== baseline.afford.verdict}
            />
            <Row label="Premium" value={`${usd(result.premium)}/yr`} />
            <Row label="Premium-to-income" value={pct(result.afford.pti, 1)} />
            <Row
              label="Cover multiple"
              value={`${result.afford.cov_mult.toFixed(1)}× / ${result.afford.cov_cap}×`}
            />
          </dl>

          <div className="whatif__why">
            <span className="eyebrow">Why</span>
            <ul className="reasons">
              {result.reasons.map((r) => (
                <li key={r}>{r}</li>
              ))}
            </ul>
          </div>
        </div>
      </div>
    </section>
  )
}

function Delta({
  label,
  now = 0,
  was = 0,
  hide,
  text,
  wasText,
  cls,
  changed,
}: {
  label: string
  now?: number
  was?: number
  hide?: boolean
  text?: string
  wasText?: string
  cls?: string
  changed?: boolean
}) {
  if (hide) {
    return (
      <div className="whatif__row">
        <dt>{label}</dt>
        <dd className={cls}>
          {text}
          {changed && <span className="whatif__was"> was {wasText}</span>}
        </dd>
      </div>
    )
  }
  const diff = now - was
  return (
    <div className="whatif__row">
      <dt>{label}</dt>
      <dd className="figure">
        {now}
        {diff !== 0 && (
          <span className={diff > 0 ? 'v-fail' : 'v-pass'}>
            {' '}
            {diff > 0 ? '+' : ''}
            {diff}
          </span>
        )}
      </dd>
    </div>
  )
}

function Row({ label, value }: { label: string; value: string }) {
  return (
    <div className="whatif__row">
      <dt>{label}</dt>
      <dd className="figure">{value}</dd>
    </div>
  )
}
