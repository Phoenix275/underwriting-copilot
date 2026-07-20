import { useMemo, useRef } from 'react'
import { motion, useScroll, useSpring } from 'motion/react'
import type { ViewId } from '../App'
import { useData } from '../data/DataContext'
import type { Case, Report } from '../data/types'
import { IconArrow } from '../components/icons'
import { affordClass, pct, usd, verdictClass } from '../lib/format'
import '../styles/pipeline.css'

interface Step {
  title: string
  what: string
  /** the measured result for the whole book */
  measured: { label: string; value: string }[]
  /** what happened to the case currently open */
  forThisCase: (c: Case) => { text: string; cls?: string }
}

const buildSteps = (report: Report): Step[] => {
  const t = report.decisioning.thresholds
  return [
  {
    title: 'Read the packet',
    what:
      'Five PDFs arrive per applicant — application form, payslip, paramedical report, three-month bank statement and tax slip. Twelve fields are pulled from them and held separately from anything the applicant typed.',
    measured: [
      { label: 'Field accuracy vs printed ground truth', value: pct(report.extraction.field_level_accuracy) },
      { label: 'Packets rendered and re-read', value: String(report.n_packets) },
      { label: 'Fields checked per packet', value: String(Object.keys(report.extraction.per_field).length) },
    ],
    forThisCase: (c) =>
      c.extraction
        ? { text: `${Object.values(c.extraction).filter((v) => v != null).length} fields read from this applicant's packet.` }
        : { text: 'No packet was rendered for this applicant — the later steps ran on structured data alone.' },
  },
  {
    title: 'Screen for contradictions',
    what:
      'Six checks compare the documents against each other and against the form. Every packet gets all six, in the same order — the screen is not targeted at anyone, which is the only way a clean result carries information.',
    measured: [
      { label: 'Recall on injected conflicts', value: pct(report.conflict_screening.detection_recall) },
      { label: 'False positives', value: String(report.conflict_screening.fp) },
      { label: 'Conflicts caught', value: String(report.conflict_screening.tp) },
    ],
    forThisCase: (c) =>
      c.conflicts.length
        ? {
            text: `${c.conflicts.length} conflict(s) found: ${c.conflicts.map((x) => x.type.replace(/_/g, ' ')).join(', ')}.`,
            cls: 'v-fail',
          }
        : { text: 'No contradictions between the documents.', cls: c.extraction ? 'v-pass' : undefined },
  },
  {
    title: 'Score the mortality risk',
    what:
      'Two engines run on the same applicant. A weighted rule engine that can be read line by line, and a gradient-boosted model trained on the book plus priors from twenty public datasets and the published Framingham CVD model. The composite is an even split, so the model can never outvote the explainable half.',
    measured: [
      { label: 'Gradient boosting AUC', value: report.risk_models.gradient_boosting.auc.toFixed(3) },
      { label: 'Logistic regression AUC', value: report.risk_models.logistic_regression.auc.toFixed(3) },
      { label: 'Held-out test cases', value: report.risk_models.n_test.toLocaleString('en-US') },
    ],
    forThisCase: (c) => ({
      text: `Rule engine ${c.rule_score}, gradient boosting ${c.ml_score.toFixed(0)} → composite ${c.risk_score}/100, tier ${c.tier}.`,
      cls: verdictClass(c.verdict),
    }),
  },
  {
    title: 'Screen the affordability',
    what:
      'Independently of any of the above, four financial-viability indicators ask whether this much cover makes sense for this income: premium-to-income, disposable income after the premium, coverage as a multiple of income against an age-banded cap, and debt service. A healthy applicant asking for far more cover than their income supports is caught here and nowhere else.',
    measured: [
      { label: 'Affordable', value: pct(report.affordability.affordable_rate) },
      { label: 'Strained', value: pct(report.affordability.strained_rate) },
      { label: 'Not justified', value: pct(report.affordability.not_justified_rate) },
    ],
    forThisCase: (c) => ({
      text: `${c.afford.label} — premium ${usd(c.afford.premium)}/yr at ${pct(c.afford.pti, 1)} of income, cover ${c.afford.cov_mult.toFixed(1)}× against a ${c.afford.cov_cap}× cap.`,
      cls: affordClass(c.afford.verdict),
    }),
  },
  {
    title: 'Decide, or hand it to a person',
    what:
      `A case clears automatically only if it is below the ${t.a_line}-point approve line, carries no conflicts, no failed affordability indicator and no disclosed special circumstance, and the two engines agree within 20 points. Anything at or above ${t.d_line} is declined. Everything else goes to a named underwriter — that referral path is the product, not a fallback.`,
    measured: [
      { label: 'Straight-through rate', value: pct(t.stp_est, 1) },
      { label: 'High-risk cases in the approve zone', value: pct(t.approve_risk_rate, 1) },
      { label: 'Decline-zone precision', value: pct(t.decline_precision, 1) },
    ],
    forThisCase: (c) => ({ text: `${c.decision} — ${c.rate_class}.`, cls: verdictClass(c.verdict) }),
  },
  ]
}

export default function Pipeline({ c, onGo }: { c: Case; onGo: (v: ViewId) => void }) {
  const { report } = useData()
  const steps = useMemo(() => buildSteps(report), [report])
  const track = useRef<HTMLOListElement>(null)
  const { scrollYProgress } = useScroll({
    target: track,
    offset: ['start 0.75', 'end 0.6'],
  })
  // the spine draws as you read down it — the one scroll-linked effect here,
  // and it maps to the thing the page is describing
  const spine = useSpring(scrollYProgress, { stiffness: 120, damping: 30, restDelta: 0.001 })

  return (
    <>
      <div className="viewhead">
        <p className="eyebrow">How it decides</p>
        <h1 className="viewhead__title">
          Five steps,
          <br />
          one of them a person
        </h1>
        <p className="viewhead__lede">
          The same five steps run on every application. Each one below shows what it does, what it
          measured across the book, and what it did to the case you have open —{' '}
          <b>{c.name}</b>.
        </p>
      </div>

      <div className="viewbody">
        <ol className="flow" ref={track}>
          <div className="flow__spine" aria-hidden="true">
            <motion.div className="flow__spine-fill" style={{ scaleY: spine }} />
          </div>

          {steps.map((s, i) => {
            const mine = s.forThisCase(c)
            return (
              <li key={s.title} className="flow__step">
                <div className="flow__marker figure" aria-hidden="true">
                  {i + 1}
                </div>

                <div className="flow__body">
                  <h2 className="flow__title">{s.title}</h2>
                  <p className="flow__what">{s.what}</p>

                  <div className="flow__measured">
                    {s.measured.map((m) => (
                      <div key={m.label} className="flow__stat">
                        <span className="figure flow__statval">{m.value}</span>
                        <span className="flow__statlabel">{m.label}</span>
                      </div>
                    ))}
                  </div>

                  <p className="flow__mine">
                    <span className="eyebrow">On this case</span>
                    <span className={mine.cls}>{mine.text}</span>
                  </p>
                </div>
              </li>
            )
          })}
        </ol>

        <div className="caseout">
          <button type="button" className="btn" onClick={() => onGo('evidence')}>
            See the evidence behind these numbers
            <IconArrow className="btn__icon" />
          </button>
          <button type="button" className="btn btn--ghost" onClick={() => onGo('case')}>
            Back to the case file
          </button>
        </div>
      </div>
    </>
  )
}
