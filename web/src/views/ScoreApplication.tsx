import { useMemo, useState } from 'react'
import { motion } from 'motion/react'
import type { Case } from '../data/types'
import DecisionStamp from '../components/DecisionStamp'
import {
  POLICY_TYPES,
  caseToApplication,
  scoreApplication,
  type Application,
} from '../lib/score'
import { affordClass, pct, usd, verdictClass } from '../lib/format'
import '../styles/score.css'

export default function ScoreApplication({ seed }: { seed: Case }) {
  const [a, setA] = useState<Application>(() => caseToApplication(seed))
  const result = useMemo(() => scoreApplication(a), [a])

  const set = <K extends keyof Application>(k: K, v: Application[K]) =>
    setA((prev) => ({ ...prev, [k]: v }))

  const num = (k: keyof Application) => (e: React.ChangeEvent<HTMLInputElement>) =>
    set(k, (Number(e.target.value) || 0) as Application[typeof k])

  return (
    <>
      <div className="viewhead">
        <p className="eyebrow">New application</p>
        <h1 className="viewhead__title">Score it now</h1>
        <p className="viewhead__lede">
          The rule engine, the logistic model, the Framingham prior and the affordability screen all
          run in this page — no server, no request. Change anything and the verdict re-derives
          immediately. Seeded from {seed.name}.
        </p>
      </div>

      <div className="viewbody score">
        <form className="score__form" onSubmit={(e) => e.preventDefault()}>
          <Group title="Applicant">
            <Field label="Name">
              <input value={a.name} onChange={(e) => set('name', e.target.value)} />
            </Field>
            <Field label="Sex">
              <select value={a.sex} onChange={(e) => set('sex', e.target.value as 'M' | 'F')}>
                <option value="M">Male</option>
                <option value="F">Female</option>
              </select>
            </Field>
            <Field label="Age" hint="years">
              <input type="number" min={18} max={80} value={a.age} onChange={num('age')} />
            </Field>
          </Group>

          <Group title="Cover requested">
            <Field label="Policy type">
              <select value={a.policy} onChange={(e) => set('policy', e.target.value)}>
                {POLICY_TYPES.map((p) => (
                  <option key={p} value={p}>
                    {p}
                  </option>
                ))}
              </select>
            </Field>
            <Field label="Face amount" hint="USD">
              <input type="number" step={50000} value={a.coverage} onChange={num('coverage')} />
            </Field>
            <Field label="Cover already in force" hint="USD">
              <input
                type="number"
                step={50000}
                value={a.existingCoverage}
                onChange={num('existingCoverage')}
              />
            </Field>
          </Group>

          <Group title="Finances">
            <Field label="Annual income" hint="USD">
              <input type="number" step={5000} value={a.income} onChange={num('income')} />
            </Field>
            <Field label="Monthly expenses" hint="USD">
              <input
                type="number"
                step={100}
                value={Math.round(a.monthlyExpenses)}
                onChange={num('monthlyExpenses')}
              />
            </Field>
            <Field label="Outstanding debt" hint="USD">
              <input type="number" step={5000} value={a.debt} onChange={num('debt')} />
            </Field>
            <Field label="Credit score">
              <input type="number" min={300} max={850} value={a.credit} onChange={num('credit')} />
            </Field>
          </Group>

          <Group title="Health">
            <Field label="Tobacco">
              <select
                value={a.smoker}
                onChange={(e) => set('smoker', e.target.value as Application['smoker'])}
              >
                <option>Non-smoker</option>
                <option>Former smoker</option>
                <option>Smoker</option>
              </select>
            </Field>
            <Field label="Body mass index">
              <input
                type="number"
                step={0.1}
                min={14}
                max={55}
                value={a.bmi}
                onChange={num('bmi')}
              />
            </Field>
            <Field label="Systolic blood pressure" hint="mmHg">
              <input type="number" min={80} max={220} value={a.systolic} onChange={num('systolic')} />
            </Field>
            <Field label="Total cholesterol" hint="mg/dL">
              <input
                type="number"
                min={100}
                max={400}
                value={a.cholesterol}
                onChange={num('cholesterol')}
              />
            </Field>
            <Field label="Existing conditions" hint="comma separated, or None">
              <input value={a.conditions} onChange={(e) => set('conditions', e.target.value)} />
            </Field>
          </Group>

          <Group title="Lifestyle">
            <Field label="Hazardous activity" hint="or None">
              <input value={a.hazard} onChange={(e) => set('hazard', e.target.value)} />
            </Field>
            <Field label="Driving violations" hint="last 3 years">
              <input type="number" min={0} max={10} value={a.violations} onChange={num('violations')} />
            </Field>
            <Field label="Alcohol use">
              <select
                value={a.alcohol}
                onChange={(e) => set('alcohol', e.target.value as Application['alcohol'])}
              >
                <option>None</option>
                <option>Moderate</option>
                <option>Heavy</option>
              </select>
            </Field>
          </Group>

          <Group title="Declarations">
            <div className="score__checks">
              <Check label="Family medical history" k="familyHistory" a={a} set={set} />
              <Check label="Insurance previously declined or rated" k="priorDecline" a={a} set={set} />
              <Check label="Careless or dangerous driving" k="dangerousDriving" a={a} set={set} />
              <Check label="Drug use or counselling" k="drugUse" a={a} set={set} />
              <Check label="Criminal offence" k="criminalRecord" a={a} set={set} />
              <Check label="Bankruptcy" k="bankruptcy" a={a} set={set} />
              <Check label="Foreign travel planned" k="foreignTravel" a={a} set={set} />
              <Check label="Weight change over 10 lb" k="weightChange" a={a} set={set} />
            </div>
            <Field label="Unique circumstances" hint="anything disclosed here refers the case">
              <input
                value={a.unique}
                placeholder="Leave blank if none"
                onChange={(e) => set('unique', e.target.value)}
              />
            </Field>
          </Group>

          <div className="score__reset">
            <button
              type="button"
              className="btn btn--ghost"
              onClick={() => setA(caseToApplication(seed))}
            >
              Reset to {seed.name}
            </button>
          </div>
        </form>

        {/* ---- live result ---- */}
        <aside className="score__out" aria-live="polite">
          <div className="score__stamp">
            <DecisionStamp
              key={result.decision}
              verdict={result.verdict}
              decision={result.decision}
              rateClass={result.rate_class}
            />
          </div>

          <div className="score__scores">
            <Big label="Composite risk" value={String(result.risk_score)} cls={verdictClass(result.verdict)} />
            <Big
              label="Affordability"
              value={result.afford.label}
              cls={affordClass(result.afford.verdict)}
              small
            />
          </div>

          <dl className="kv">
            <Row k="Rule engine" v={String(result.ruleScore)} />
            <Row k="Logistic model" v={result.mlScore.toFixed(1)} />
            <Row k="Framingham 10-yr CVD" v={pct(result.publishedPrior, 1)} />
            <Row k="Public-dataset prior" v={pct(result.externalPrior, 1)} />
            <Row k="Indicative premium" v={`${usd(result.premium)}/yr`} />
            <Row k="Premium-to-income" v={pct(result.afford.pti, 1)} />
            <Row k="Cover multiple" v={`${result.afford.cov_mult.toFixed(1)}× / ${result.afford.cov_cap}×`} />
          </dl>

          <div className="score__ind">
            {result.afford.indicators.map((i) => (
              <div key={i.label} className={`score__indrow ${affordClass(i.status)}`}>
                <span>{i.label}</span>
                <span className="figure">{i.value}</span>
              </div>
            ))}
          </div>

          <div className="score__why">
            <span className="eyebrow">Why</span>
            <ul className="reasons">
              {result.reasons.map((r, i) => (
                <motion.li
                  key={r}
                  initial={{ opacity: 0, x: -6 }}
                  animate={{ opacity: 1, x: 0 }}
                  transition={{ duration: 0.25, delay: i * 0.04 }}
                >
                  {r}
                </motion.li>
              ))}
            </ul>
          </div>

          <p className="score__note">
            Two things differ from a full pipeline run. The composite uses the logistic regression,
            because a gradient-boosted ensemble cannot be shipped as coefficients — expect a few
            points either way against the portfolio figures. And the cross-document conflict checks
            cannot run at all, since they compare a rendered PDF packet against the form and this
            application has no documents attached.
          </p>
        </aside>
      </div>
    </>
  )
}

function Group({ title, children }: { title: string; children: React.ReactNode }) {
  return (
    <fieldset className="fgroup">
      <legend className="eyebrow">{title}</legend>
      <div className="fgroup__body">{children}</div>
    </fieldset>
  )
}

function Field({
  label,
  hint,
  children,
}: {
  label: string
  hint?: string
  children: React.ReactNode
}) {
  return (
    <label className="field">
      <span className="field__label">
        {label}
        {hint && <span className="field__hint"> {hint}</span>}
      </span>
      {children}
    </label>
  )
}

function Check({
  label,
  k,
  a,
  set,
}: {
  label: string
  k: keyof Application
  a: Application
  set: <K extends keyof Application>(k: K, v: Application[K]) => void
}) {
  return (
    <label className="check">
      <input
        type="checkbox"
        checked={Boolean(a[k])}
        onChange={(e) => set(k, e.target.checked as Application[typeof k])}
      />
      <span>{label}</span>
    </label>
  )
}

function Big({
  label,
  value,
  cls,
  small,
}: {
  label: string
  value: string
  cls: string
  small?: boolean
}) {
  return (
    <div className="big">
      <span className="eyebrow">{label}</span>
      <motion.span
        key={value}
        initial={{ opacity: 0, y: 6 }}
        animate={{ opacity: 1, y: 0 }}
        transition={{ duration: 0.2 }}
        className={`figure big__value${small ? ' big__value--sm' : ''} ${cls}`}
      >
        {value}
      </motion.span>
    </div>
  )
}

function Row({ k, v }: { k: string; v: string }) {
  return (
    <div className="kv__row">
      <dt>{k}</dt>
      <dd className="figure">{v}</dd>
    </div>
  )
}
