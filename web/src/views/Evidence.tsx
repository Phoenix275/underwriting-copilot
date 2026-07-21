import { useData } from '../data/DataContext'
import type { FairnessRow, Report } from '../data/types'
import {
  aucBenchmarks,
  weightSources,
  weightValidation,
  coverageMultiples,
  coverageSources,
  disclosureBenchmarks,
  obligations,
  stpBenchmarks,
  unverified,
  type Benchmark,
} from '../data/benchmarks'
import { pct } from '../lib/format'
import '../styles/evidence.css'

export default function Evidence() {
  const { report } = useData()
  const t = report.decisioning.thresholds
  const rm = report.risk_models
  const datasets = report.external_learning.datasets

  return (
    <>
      <div className="viewhead">
        <p className="eyebrow">Evidence · model card</p>
        <h1 className="viewhead__title">
          What this
          <br />
          actually proves
        </h1>
        <p className="viewhead__lede">
          Every result here is measured, and every industry figure it is compared against is cited.
          Where the industry publishes no number, this page says so rather than inventing one.
        </p>
      </div>

      <div className="viewbody">
        {/* ---- headline ---- */}
        <div className="srule">
          <span className="eyebrow">Measured on this build</span>
        </div>

        <div className="ecards">
          <ECard
            value={rm.gradient_boosting.auc.toFixed(3)}
            label="Gradient boosting AUC"
            note={`on ${rm.n_test.toLocaleString('en-US')} held-out cases`}
          />
          <ECard
            value={pct(report.extraction.field_level_accuracy)}
            label="Extraction accuracy"
            note={`${Object.keys(report.extraction.per_field).length} fields × ${report.n_packets} packets`}
          />
          <ECard
            value={pct(report.conflict_screening.detection_recall)}
            label="Conflict recall"
            note={`${report.conflict_screening.fp} false positives`}
          />
          <ECard
            value={pct(t.stp_est, 1)}
            label="Straight-through rate"
            note={t.evaluation}
          />
        </div>

        {/* ---- the honest AUC framing ---- */}
        <div className="srule">
          <span className="eyebrow">Where an AUC of {rm.gradient_boosting.auc.toFixed(2)} sits</span>
        </div>

        <div className="warn">
          <h2 className="warn__title">Read this before quoting the AUC</h2>
          <p>
            This model scores <b>above every published life-underwriting benchmark below</b>, and
            that is a warning rather than a result. The label it predicts is authored by the same
            synthetic generator that produced the features, so the model is partly re-deriving a
            known rule rather than predicting mortality. On real applicants, published models reach{' '}
            <b>0.71 – 0.74</b>. Treat {rm.gradient_boosting.auc.toFixed(3)} as evidence that the
            pipeline works end to end, not as evidence of predictive skill.
          </p>
        </div>

        <div className="bench">
          {aucBenchmarks.map((b) => (
            <BenchRow key={b.label} b={b} />
          ))}
          <div className="bench__row bench__row--ours">
            <div className="bench__main">
              <span className="bench__label">This build, synthetic book with an authored label</span>
              <span className="bench__src">Not comparable to the rows above</span>
            </div>
            <span className="figure bench__value">
              {rm.gradient_boosting.auc.toFixed(3)} / {rm.logistic_regression.auc.toFixed(3)}
            </span>
          </div>
        </div>

        {/* ---- where the weights come from ---- */}
        <div className="srule">
          <span className="eyebrow">Where the risk weights come from</span>
        </div>

        <p className="sectionlede">
          The rule engine&rsquo;s medical weights are not hand-picked. Each is{' '}
          <span className="figure">round(28 × ln(mortality multiple))</span> — so the ratio between
          any two points is the ratio between two real relative-mortality figures, drawn from linked
          death records and large published cohorts.
        </p>

        <div className="weights">
          <div className="weights__head">
            <span>Factor</span>
            <span className="queue__num">Points</span>
            <span className="queue__num">Real multiple</span>
            <span>Source</span>
          </div>
          {weightSources.map((w) => (
            <div key={w.factor} className="weights__row">
              <span className="weights__factor">{w.factor}</span>
              <span className="figure queue__num">{w.points}</span>
              <span className="figure queue__num">{w.multiple}</span>
              <span className="weights__src">
                <a href={w.url} target="_blank" rel="noopener noreferrer">
                  {w.source}
                </a>
                <span className="weights__detail">{w.detail}</span>
              </span>
            </div>
          ))}
        </div>

        <p className="footnote">{weightValidation.prudential}</p>
        <p className="footnote">{weightValidation.note}</p>

        {/* ---- calibration ---- */}
        <div className="srule">
          <span className="eyebrow">Calibration</span>
        </div>

        <p className="sectionlede">
          A risk score is only useful if it means what it says. Each bar compares the score the
          model gave to the share of those cases that were actually high risk.
        </p>

        <Calibration bins={rm.calibration} />

        {/* ---- STP context ---- */}
        <div className="srule">
          <span className="eyebrow">Straight-through rate in context</span>
        </div>

        <p className="sectionlede">
          Straight-through processing — the share of applications decided without a human — is the
          headline operational metric, so the thresholds are tuned to maximise it. That is a choice
          with a cost, and the cost is shown here rather than hidden. Nothing in this tuning touches
          the conflict, affordability or engine-disagreement gates: those still force a referral
          regardless of score.
        </p>

        <div className="tradeoff">
          <div className="tradeoff__cell">
            <span className="figure tradeoff__now v-pass">{pct(t.stp_est, 1)}</span>
            <span className="tradeoff__label">Straight-through rate</span>
            <span className="tradeoff__note">the lever was pulled for this</span>
          </div>
          <div className="tradeoff__cell">
            <span className="figure tradeoff__now">{pct(t.approve_risk_rate, 1)}</span>
            <span className="tradeoff__label">High-risk in the auto-approve zone</span>
            <span className="tradeoff__note">essentially unchanged — approve-side safety held</span>
          </div>
          <div className="tradeoff__cell">
            <span className="figure tradeoff__now v-watch">{pct(t.decline_precision, 1)}</span>
            <span className="tradeoff__label">Auto-decline precision</span>
            <span className="tradeoff__note">the metric that was sacrificed</span>
          </div>
        </div>

        <p className="footnote">
          The search is unconstrained — no ceiling on approve-zone risk, no floor under the decline
          line. The one guard is a minimum auto-decline precision of 50%, and it is there to stop
          the optimiser gaming the metric rather than to balance the model: with no floor at all the
          maximum is to auto-decline the entire book (STP≈100%, but it rejects every customer and
          leaves nothing to underwrite). With that single guard, STP settles at{' '}
          {pct(t.stp_est, 1)}. The price is auto-decline precision: about{' '}
          {pct(1 - t.decline_precision, 0)} of auto-declines are applicants who were not actually
          high-risk. In a real system those would still route to a decline rate class a person can
          appeal, not a hard rejection — but the false-decline rate is real and is the reason to
          watch this number. Auto-approve-zone risk, by contrast, stayed low, and the referrals it
          leaves are routed to underwriters by difficulty.
        </p>

        <div className="bench">
          {stpBenchmarks.map((b) => (
            <BenchRow key={b.label} b={b} />
          ))}
          <div className="bench__row bench__row--ours">
            <div className="bench__main">
              <span className="bench__label">This build — auto-decided share of the book</span>
              <span className="bench__src">
                {t.evaluation} · approve &lt;{t.a_line}, decline ≥{t.d_line}
              </span>
            </div>
            <span className="figure bench__value">{pct(t.stp_est, 1)}</span>
          </div>
        </div>

        {/* ---- fairness ---- */}
        <div className="srule">
          <span className="eyebrow">Fairness audit</span>
        </div>

        <p className="sectionlede">
          Outcome mix alone hides unfairness: a group can receive a reasonable spread of verdicts
          while carrying a much larger share of the model's mistakes. Both are shown. Age is a
          priced factor in life insurance and a steep gradient is expected; the sex gradient is
          audited because sex feeds both the Framingham and public-dataset priors.
        </p>

        <FairTable title="By age band" rows={report.fairness_by_age} />
        <FairTable title="By sex" rows={report.fairness_by_sex} />

        <p className="footnote">
          The false-negative rate falls and the false-positive rate rises steeply with age. That is
          the model's error budget shifting, not just its verdicts — a 61–70 applicant is far more
          likely to be wrongly flagged high risk than a 21–30 applicant is. Any production use would
          have to justify that gradient against the underlying mortality curve.
        </p>

        {/* ---- affordability thresholds ---- */}
        <div className="srule">
          <span className="eyebrow">Affordability thresholds</span>
        </div>

        <p className="sectionlede">
          The coverage-multiple cap is modelled on published carrier guidance. The other three
          thresholds are not — no insurer publishes a premium-to-income or debt-service standard for
          life cover, so those are stated design choices and labelled as such throughout.
        </p>

        <div className="capgrid">
          <div className="capgrid__head">
            <span>Age band</span>
            <span className="queue__num">Brighthouse</span>
            <span className="queue__num">Pacific Life</span>
            <span className="queue__num">This build</span>
          </div>
          {coverageMultiples.map((r) => (
            <div key={r.age} className="capgrid__row">
              <span>{r.age}</span>
              <span className="figure queue__num">{r.brighthouse}×</span>
              <span className="figure queue__num">{r.pacificLife}×</span>
              <span className="figure queue__num">{r.ours}×</span>
            </div>
          ))}
        </div>

        <div className="sources">
          {coverageSources.map((s) => (
            <a key={s.label} href={s.url} target="_blank" rel="noopener noreferrer">
              {s.label} →
            </a>
          ))}
        </div>

        {/* ---- non-disclosure ---- */}
        <div className="srule">
          <span className="eyebrow">Non-disclosure, as measured by the industry</span>
        </div>

        <div className="bench">
          {disclosureBenchmarks.map((b) => (
            <BenchRow key={b.label} b={b} />
          ))}
        </div>

        {/* ---- public datasets ---- */}
        <div className="srule">
          <span className="eyebrow">Public datasets behind the prior</span>
        </div>

        <p className="sectionlede">
          Twenty public datasets each train a small model whose vote is weighted by how far its AUC
          beats chance. Datasets at or near chance are excluded outright and shown here greyed —
          averaging them in would have quietly diluted the signal.
        </p>

        <div className="dsets">
          {datasets.map((d) => (
            <div key={d.name} className={`dset${d.included_in_prior ? '' : ' is-out'}`}>
              <div className="dset__top">
                <span className="dset__name">{d.name}</span>
                <span className="figure dset__auc">{d.auc.toFixed(3)}</span>
              </div>
              <div className="dset__meta">
                {d.rows.toLocaleString('en-US')} rows · {d.features.join(', ')}
                {!d.included_in_prior && <span className="dset__out"> · excluded, at chance</span>}
              </div>
            </div>
          ))}
        </div>

        {/* ---- governance ---- */}
        <div className="srule">
          <span className="eyebrow">Regulatory position</span>
        </div>

        <p className="sectionlede">
          Life-insurance risk assessment is a regulated use of AI in every jurisdiction below. This
          is what each regime asks for and what this build honestly does about it.
        </p>

        <div className="obs">
          {obligations.map((o) => (
            <article key={o.regime} className={`ob ob--${o.met}`}>
              <header className="ob__head">
                <h3 className="ob__regime">{o.regime}</h3>
                <span className={`ob__badge ob__badge--${o.met}`}>
                  {o.met === 'partial' ? 'Partly met' : o.met === 'design' ? 'Met by design' : 'Not claimed'}
                </span>
              </header>
              <p className="ob__status">{o.status}</p>
              <ul className="ob__req">
                {o.requires.map((r) => (
                  <li key={r}>{r}</li>
                ))}
              </ul>
              <p className="ob__pos">{o.position}</p>
              <a className="ob__link" href={o.url} target="_blank" rel="noopener noreferrer">
                Primary source →
              </a>
            </article>
          ))}
        </div>

        {/* ---- limits ---- */}
        <div className="srule">
          <span className="eyebrow">What could not be verified</span>
        </div>

        <ul className="limits">
          {unverified.map((u) => (
            <li key={u}>{u}</li>
          ))}
          <li>
            The book is synthetic. It proves the pipeline, not production risk weights. Rule weights
            need validating against a real underwriting manual before any of this means anything
            about a real applicant.
          </li>
          <li>
            Extraction scores {pct(report.extraction.field_level_accuracy)} because the PDFs are
            generated with a digital text layer. On scanned paper it will drop, which is the gap a
            document-AI service closes.
          </li>
        </ul>

        <p className="casefoot eyebrow">
          Pipeline run {report.generated_at} · {report.n_applicants.toLocaleString('en-US')}{' '}
          applicants · {report.n_packets} packets · seed-reproducible
        </p>
      </div>
    </>
  )
}

function ECard({ value, label, note }: { value: string; label: string; note: string }) {
  return (
    <div className="ecard">
      <span className="figure ecard__value">{value}</span>
      <span className="ecard__label">{label}</span>
      <span className="ecard__note">{note}</span>
    </div>
  )
}

function BenchRow({ b }: { b: Benchmark }) {
  return (
    <div className="bench__row">
      <div className="bench__main">
        <span className="bench__label">{b.label}</span>
        <span className="bench__src">
          <a href={b.url} target="_blank" rel="noopener noreferrer">
            {b.source}
          </a>{' '}
          · {b.year}
          {b.note && <> · {b.note}</>}
        </span>
      </div>
      <span className="figure bench__value">{b.value}</span>
    </div>
  )
}

function FairTable({ title, rows }: { title: string; rows: FairnessRow[] }) {
  return (
    <div className="fair">
      <div className="fair__head">
        <span>{title}</span>
        <span className="queue__num">n</span>
        <span className="queue__num">Approve</span>
        <span className="queue__num">Refer</span>
        <span className="queue__num">Decline</span>
        <span className="queue__num">FPR</span>
        <span className="queue__num">FNR</span>
      </div>
      {rows.map((r) => (
        <div key={r.band} className="fair__row">
          <span>{r.band}</span>
          <span className="figure queue__num">{r.n.toLocaleString('en-US')}</span>
          <span className="figure queue__num v-pass">{pct(r.green)}</span>
          <span className="figure queue__num v-watch">{pct(r.yellow)}</span>
          <span className="figure queue__num v-fail">{pct(r.red)}</span>
          <span className="figure queue__num">{pct(r.model_fpr, 1)}</span>
          <span className="figure queue__num">{pct(r.model_fnr, 1)}</span>
        </div>
      ))}
    </div>
  )
}

function Calibration({ bins }: { bins: Report['risk_models']['calibration'] }) {
  const W = 640
  const H = 220
  const pad = { l: 34, r: 8, t: 10, b: 26 }
  const iw = W - pad.l - pad.r
  const ih = H - pad.t - pad.b
  const bw = iw / bins.length

  return (
    <div className="calib">
      <svg viewBox={`0 0 ${W} ${H}`} className="calib__svg" role="img"
        aria-label="Calibration: predicted risk against observed high-risk rate, by decile bin.">
        {[0, 0.25, 0.5, 0.75, 1].map((g) => (
          <g key={g}>
            <line
              x1={pad.l}
              x2={W - pad.r}
              y1={pad.t + ih * (1 - g)}
              y2={pad.t + ih * (1 - g)}
              className="calib__grid"
            />
            <text x={pad.l - 7} y={pad.t + ih * (1 - g)} className="calib__tick" textAnchor="end"
              dominantBaseline="middle">
              {Math.round(g * 100)}
            </text>
          </g>
        ))}

        {bins.map((b, i) => {
          const x = pad.l + i * bw
          return (
            <g key={b.bin}>
              <rect
                x={x + bw * 0.16}
                y={pad.t + ih * (1 - b.actual)}
                width={bw * 0.68}
                height={ih * b.actual}
                className="calib__bar"
              />
              <text x={x + bw / 2} y={H - 8} className="calib__tick" textAnchor="middle">
                {b.bin.replace('–', '-').replace('%', '')}
              </text>
            </g>
          )
        })}

        {/* what perfect calibration would look like */}
        <path
          className="calib__ideal"
          d={bins
            .map(
              (b, i) =>
                `${i === 0 ? 'M' : 'L'}${pad.l + i * bw + bw / 2} ${pad.t + ih * (1 - b.predicted)}`,
            )
            .join('')}
        />
        {bins.map((b, i) => (
          <circle
            key={b.bin}
            cx={pad.l + i * bw + bw / 2}
            cy={pad.t + ih * (1 - b.predicted)}
            r={2.6}
            className="calib__dot"
          />
        ))}
      </svg>
      <p className="calib__legend">
        <span className="calib__key calib__key--bar" /> observed high-risk rate
        <span className="calib__key calib__key--line" /> predicted risk · x-axis: predicted band (%)
      </p>
    </div>
  )
}
