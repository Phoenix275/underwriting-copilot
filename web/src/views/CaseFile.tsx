import { motion } from 'motion/react'
import type { ViewId } from '../App'
import { useData } from '../data/DataContext'
import type { Case } from '../data/types'
import DecisionPanel from '../components/DecisionPanel'
import DecisionStamp from '../components/DecisionStamp'
import { IconArrow } from '../components/icons'
import { affordClass, pct, shortDecision, usd, usdShort, verdictClass } from '../lib/format'
import { strainScore } from '../lib/plane'
import '../styles/case.css'

const CHECK_NAMES: Record<string, string> = {
  income_mismatch: 'Declared income vs payslip',
  smoker_nondisclosure: 'Tobacco declaration vs cotinine',
  dob_mismatch: 'Date of birth vs paramedical ID',
  debt_understated: 'Declared debt vs credit bureau',
  income_deposit_mismatch: 'Payslip income vs bank deposits',
  tax_income_mismatch: 'Declared income vs tax slip',
}

const ALL_CHECKS = Object.keys(CHECK_NAMES)

export default function CaseFile({
  c,
  onOpen,
  onGo,
}: {
  c: Case
  onOpen: (id: string) => void
  onGo: (v: ViewId) => void
}) {
  const { cases, report } = useData()
  const idx = cases.findIndex((x) => x.id === c.id)
  const prev = cases[idx - 1]
  const next = cases[idx + 1]

  return (
    <>
      <div className="viewhead">
        <div className="casenav">
          <button
            type="button"
            className="btn btn--ghost"
            disabled={!prev}
            onClick={() => prev && onOpen(prev.id)}
          >
            ← Previous
          </button>
          <span className="eyebrow">
            Case {idx + 1} of {cases.length}, in ascending risk order
          </span>
          <button
            type="button"
            className="btn btn--ghost"
            disabled={!next}
            onClick={() => next && onOpen(next.id)}
          >
            Next →
          </button>
        </div>
      </div>

      <div className="viewbody">
        <motion.header
          className="casehead"
          key={c.id}
          initial={{ opacity: 0, y: 10 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.3 }}
        >
          <div className="casehead__who">
            <p className="eyebrow">
              {c.id} · {c.policy}
            </p>
            <h1 className="casehead__name">{c.name}</h1>
            <p className="casehead__meta">
              {c.age}, {c.sex === 'M' ? 'male' : 'female'} · {c.occupation} at {c.employer} ·{' '}
              {c.city}, {c.state}
            </p>
            <p className="casehead__meta">
              Applying for <b>{usd(c.coverage)}</b> of cover
              {c.existing_cov > 0 && <> alongside {usdShort(c.existing_cov)} already in force</>} ·
              indicative premium <b>{usd(c.premium)}</b> a year
            </p>
          </div>
          <DecisionStamp verdict={c.verdict} decision={c.decision} rateClass={c.rate_class} />
        </motion.header>

        {/* ---- the two questions, side by side ---- */}
        <div className="srule">
          <span className="eyebrow">The two questions</span>
        </div>

        <div className="dual">
          <section className="dual__col panel">
            <div className="panel__head">
              <h2 className="panel__title">Is the risk insurable?</h2>
              <span className={`figure dual__score ${verdictClass(c.verdict)}`}>
                {c.risk_score}
                <span className="dual__of">/100</span>
              </span>
            </div>
            <div className="panel__body">
              <p className="dual__lede">
                An explainable rule engine and a gradient-boosted model, weighted evenly. Tier{' '}
                <b>{c.tier}</b>.
              </p>

              <Bar label="Rule engine" value={c.rule_score} />
              <Bar label="Gradient boosting" value={c.ml_score} />
              <Bar label="Logistic regression" value={c.ml_score_lr} />

              {Math.abs(c.rule_score - c.ml_score) > 20 && (
                <p className="dual__note">
                  The engines disagree by {Math.abs(Math.round(c.rule_score - c.ml_score))} points.
                  That alone routes the case to a human.
                </p>
              )}

              <dl className="kv">
                <Kv k="Framingham 10-year CVD" v={pct(c.pub_prior, 1)} />
                <Kv k="Public-dataset prior" v={pct(c.ext_prior, 1)} />
                <Kv k="Blood pressure" v={c.bp} />
                <Kv k="Body mass index" v={c.bmi.toFixed(1)} />
                <Kv k="Tobacco" v={c.smoker} />
                <Kv k="Conditions" v={c.conditions || 'None'} />
              </dl>
            </div>
          </section>

          <section className="dual__col panel">
            <div className="panel__head">
              <h2 className="panel__title">Is the cover affordable?</h2>
              <span className={`dual__verdict ${affordClass(c.afford.verdict)}`}>
                {c.afford.label}
              </span>
            </div>
            <div className="panel__body">
              <p className="dual__lede">
                Four financial-viability indicators, independent of mortality risk. One failure
                refers the case to financial underwriting. Strain {Math.round(strainScore(c))}/100.
              </p>

              <ul className="ind">
                {c.afford.indicators.map((i) => (
                  <li key={i.label} className={`ind__row ${affordClass(i.status)}`}>
                    <div className="ind__top">
                      <span className="ind__label">{i.label}</span>
                      <span className="figure ind__value">{i.value}</span>
                    </div>
                    <p className="ind__detail">{i.detail}</p>
                  </li>
                ))}
              </ul>
            </div>
          </section>
        </div>

        {/* ---- basis ---- */}
        <div className="srule">
          <span className="eyebrow">Basis for the decision</span>
        </div>

        <div className="panel">
          <div className="panel__body">
            <ul className="reasons">
              {c.reasons.map((r, i) => (
                <li key={i}>{r}</li>
              ))}
            </ul>
            {c.unique && (
              <div className="casenote">
                <span className="eyebrow">Unique circumstances disclosed</span>
                <p>“{c.unique}”</p>
              </div>
            )}
          </div>
        </div>

        {/* ---- conflict screen ---- */}
        <div className="srule">
          <span className="eyebrow">Cross-document screen</span>
        </div>

        <p className="sectionlede">
          {c.extraction ? (
            <>
              All six checks run on every packet, in the same order, whoever the applicant is. That
              is what makes a clean result mean anything.
            </>
          ) : (
            <>
              These checks compare figures across documents, and this case has no document packet —
              so the clean result below is the absence of evidence, not evidence of absence.
            </>
          )}
        </p>

        <ul className={`checks${c.extraction ? '' : ' is-inert'}`}>
          {ALL_CHECKS.map((k) => {
            const hit = c.conflicts.find((x) => x.type === k)
            return (
              <li key={k} className={`checks__row${hit ? ' is-hit' : ''}`}>
                <span className={`checks__mark ${hit ? 'v-fail' : 'v-pass'}`} aria-hidden="true">
                  {hit ? '✕' : '✓'}
                </span>
                <div className="checks__body">
                  <span className="checks__name">{CHECK_NAMES[k]}</span>
                  {hit && <p className="checks__desc">{hit.description}</p>}
                </div>
                {hit && (
                  <span
                    className={`checks__sev ${hit.severity === 'major' ? 'v-fail' : 'v-watch'}`}
                  >
                    {hit.severity}
                  </span>
                )}
              </li>
            )
          })}
        </ul>

        {/* ---- what was read ---- */}
        <div className="srule">
          <span className="eyebrow">Read from the packet</span>
        </div>

        {c.extraction ? (
          <>
            <p className="sectionlede">
              Every figure below was extracted from a PDF rather than typed in. The screen above
              compares them against each other.
            </p>

            <div className="docs">
              <DocCard
                title="Application form"
                rows={[
                  ['Name', c.extraction.name],
                  ['Date of birth', c.extraction.form_dob],
                  ['Declared income', money(c.extraction.form_income)],
                  ['Declared debt', money(c.extraction.form_debt)],
                  ['Tobacco', c.extraction.form_tobacco_yes ? 'Yes' : 'No'],
                ]}
              />
              <DocCard
                title="Payslip"
                rows={[
                  ['Name', c.extraction.payslip_name],
                  ['Annualised income', money(c.extraction.payslip_income)],
                  ['Employment', c.extraction.employment_status],
                ]}
              />
              <DocCard
                title="Paramedical report"
                rows={[
                  ['Date of birth on ID', c.extraction.paramed_dob],
                  [
                    'Height and weight',
                    `${c.extraction.height_cm} cm · ${c.extraction.weight_kg} kg`,
                  ],
                  ['Blood pressure', c.extraction.blood_pressure],
                  ['Cholesterol', c.extraction.cholesterol],
                  ['Cotinine', c.extraction.cotinine],
                ]}
              />
              <DocCard
                title="Bank statement"
                rows={[
                  ['Monthly deposits', money(c.extraction.bank_deposit_monthly)],
                  ['Monthly outflow', money(c.extraction.bank_outflow_monthly)],
                  ['Closing balance', money(c.extraction.bank_closing_balance)],
                ]}
              />
              <DocCard
                title="Tax slip"
                rows={[
                  ['Tax year', c.extraction.tax_year],
                  ['Income reported', money(c.extraction.tax_income)],
                ]}
              />
              <DocCard
                title="Credit bureau"
                rows={[
                  ['Debt on file', money(c.extraction.bureau_debt)],
                  ['Credit score', c.credit],
                  ['Debt-to-income', pct(c.dti, 1)],
                ]}
              />
            </div>
          </>
        ) : (
          <div className="panel">
            <div className="panel__body">
              <p className="sectionlede" style={{ margin: 0 }}>
                No document packet was rendered for this applicant. {report.n_packets} of the{' '}
                {cases.length} cases in this book have PDFs behind them; the rest were scored from
                structured data alone, so the cross-document screen above has nothing to compare
                and reports clean by default. Open a case marked with a conflict flag in the queue
                to see the screen actually working.
              </p>
            </div>
          </div>
        )}

        {/* ---- rule breakdown ---- */}
        <div className="srule">
          <span className="eyebrow">Rule engine, factor by factor</span>
        </div>

        <p className="sectionlede">
          Every point in the rule score is attributable. This is the layer a manager or a regulator
          can argue with, which is why it carries half the composite.
        </p>

        <div className="factors">
          {c.rule_factors
            .slice()
            .sort((a, b) => b[2] - a[2])
            .map(([label, value, pts]) => (
              <div key={label} className={`factors__row${pts > 0 ? '' : ' is-zero'}`}>
                <span className="factors__label">{label}</span>
                <span className="factors__value">{value}</span>
                <span className="figure factors__pts">{pts > 0 ? `+${pts}` : '—'}</span>
              </div>
            ))}
          <div className="factors__row factors__row--total">
            <span className="factors__label">Rule score</span>
            <span className="factors__value" />
            <span className="figure factors__pts">{c.rule_score}</span>
          </div>
        </div>

        <div className="srule">
          <span className="eyebrow">The human decision</span>
        </div>

        <DecisionPanel caseId={c.id} />

        <div className="caseout">
          <button type="button" className="btn" onClick={() => onGo('pipeline')}>
            See how this decision was reached
            <IconArrow className="btn__icon" />
          </button>
          <button type="button" className="btn btn--ghost" onClick={() => onGo('score')}>
            Score a variation of this application
          </button>
        </div>

        <p className="casefoot eyebrow">
          Approve line {report.decisioning.thresholds.a_line} · decline line{' '}
          {report.decisioning.thresholds.d_line} · both tuned on a held-out half of the book ·
          outcome {shortDecision(c.decision)}
        </p>
      </div>
    </>
  )
}

function money(v: unknown) {
  return typeof v === 'number' ? usd(v) : ((v as string) ?? '—')
}

function Bar({ label, value }: { label: string; value: number }) {
  return (
    <div className="bar">
      <div className="bar__top">
        <span className="bar__label">{label}</span>
        <span className="figure bar__value">{Number.isInteger(value) ? value : value.toFixed(1)}</span>
      </div>
      <div className="bar__track">
        <motion.div
          className="bar__fill"
          initial={{ scaleX: 0 }}
          animate={{ scaleX: Math.min(value, 100) / 100 }}
          transition={{ duration: 0.55, ease: [0.16, 0.84, 0.28, 1] }}
        />
      </div>
    </div>
  )
}

function Kv({ k, v }: { k: string; v: string }) {
  return (
    <div className="kv__row">
      <dt>{k}</dt>
      <dd className="figure">{v}</dd>
    </div>
  )
}

function DocCard({ title, rows }: { title: string; rows: [string, unknown][] }) {
  return (
    <div className="doc">
      <h3 className="doc__title">{title}</h3>
      <dl className="doc__rows">
        {rows.map(([k, v]) => (
          <div key={k} className="doc__row">
            <dt>{k}</dt>
            <dd className="figure">{v == null || v === '' ? '—' : String(v)}</dd>
          </div>
        ))}
      </dl>
    </div>
  )
}
