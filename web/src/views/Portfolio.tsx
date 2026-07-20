import { useMemo, useState } from 'react'
import { cases, report } from '../data'
import type { Case } from '../data/types'
import PortfolioPlane from '../components/PortfolioPlane'
import { FILTERS, matchesFilter, strainScore, type PortfolioFilter } from '../lib/plane'
import { pct, shortDecision, usdShort, verdictClass, affordClass } from '../lib/format'
import '../styles/plane.css'
import '../styles/queue.css'

const t = report.decisioning.thresholds

export default function Portfolio({
  onOpen,
  selectedId,
}: {
  onOpen: (id: string) => void
  selectedId: string
}) {
  const [filter, setFilter] = useState<PortfolioFilter>('all')
  const [hovered, setHovered] = useState<Case | null>(null)

  const items = useMemo(() => cases.filter((c) => matchesFilter(c, filter)), [filter])
  const shown = hovered ?? cases.find((c) => c.id === selectedId) ?? cases[0]

  const counts = useMemo(
    () => ({
      green: cases.filter((c) => c.verdict === 'green').length,
      yellow: cases.filter((c) => c.verdict === 'yellow').length,
      red: cases.filter((c) => c.verdict === 'red').length,
    }),
    [],
  )

  return (
    <>
      <div className="hero">
        <div className="hero__say">
          <p className="eyebrow">Life insurance · financial viability</p>
          <h1 className="viewhead__title">
            Two questions,
            <br />
            asked separately
          </h1>
          <p className="viewhead__lede">
            Every application is judged twice — once on whether the risk is insurable, and once on
            whether the cover is affordable. A case can fail either one.
          </p>
        </div>

        <div className="hero__plane">
          <PortfolioPlane
            items={items}
            selectedId={selectedId}
            onOpen={onOpen}
            onHover={setHovered}
            hovered={hovered}
          />
        </div>

        <div className="hero__legend">
          <div className="planelegend">
            <Legend
              color="var(--pass)"
              label={`Auto-approve floor — risk under ${t.a_line}, affordability clear`}
            />
            <Legend
              color="var(--watch)"
              label="Financial-referral step — an affordability indicator fails"
            />
            <Legend color="var(--fail)" label={`Decline plateau — risk ${t.d_line} and above`} />
          </div>
        </div>
      </div>

      <div className="viewbody">
        <div className="planeread" aria-live="polite">
          {shown ? (
            <>
              <div>
                <div className="planeread__name">{shown.name}</div>
                <div className="planeread__meta">
                  <span className="figure">{shown.id}</span> · {shown.age}, {shown.occupation} ·{' '}
                  {usdShort(shown.coverage)} {shown.policy}
                </div>
              </div>
              <div className="planeread__scores">
                <Stat label="Risk" value={`${shown.risk_score}`} cls={verdictClass(shown.verdict)} />
                <Stat
                  label="Strain"
                  value={`${Math.round(strainScore(shown))}`}
                  cls={affordClass(shown.afford.verdict)}
                />
                <Stat
                  label="Outcome"
                  value={shortDecision(shown.decision)}
                  cls={verdictClass(shown.verdict)}
                />
              </div>
            </>
          ) : (
            <p className="planeread__empty">Hover or focus a case to read it.</p>
          )}
        </div>

        <div className="srule">
          <span className="eyebrow">The queue</span>
        </div>

        <div className="queue__filters" role="group" aria-label="Filter the queue">
          {FILTERS.map((f) => (
            <button
              key={f.id}
              type="button"
              className="chip"
              aria-pressed={filter === f.id}
              onClick={() => setFilter(f.id)}
            >
              {f.label}
              <span className="chip__n figure">
                {f.id === 'all' ? cases.length : cases.filter((c) => matchesFilter(c, f.id)).length}
              </span>
            </button>
          ))}
        </div>

        <p className="queue__summary">
          {counts.green} approve · {counts.yellow} refer · {counts.red} decline across{' '}
          {cases.length} packets. Straight-through rate {pct(t.stp_est, 1)}, measured on a held-out
          half of the book.
        </p>

        <div className="queue" role="table" aria-label="Case queue">
          <div className="queue__head" role="row">
            <span role="columnheader">Applicant</span>
            <span role="columnheader">Cover</span>
            <span role="columnheader" className="queue__num">Risk</span>
            <span role="columnheader" className="queue__num">Strain</span>
            <span role="columnheader">Affordability</span>
            <span role="columnheader">Outcome</span>
          </div>
          {items.map((c) => (
            <button
              key={c.id}
              type="button"
              role="row"
              className={`queue__row${c.id === selectedId ? ' is-selected' : ''}`}
              onClick={() => onOpen(c.id)}
              onPointerEnter={() => setHovered(c)}
              onPointerLeave={() => setHovered(null)}
            >
              <span role="cell" className="queue__who">
                <span className="queue__name">{c.name}</span>
                <span className="queue__id figure">{c.id}</span>
              </span>
              <span role="cell" className="figure queue__cover">
                {usdShort(c.coverage)}
              </span>
              <span role="cell" className={`figure queue__num ${verdictClass(c.verdict)}`}>
                {c.risk_score}
              </span>
              <span role="cell" className={`figure queue__num ${affordClass(c.afford.verdict)}`}>
                {Math.round(strainScore(c))}
              </span>
              <span role="cell" className={`queue__afford ${affordClass(c.afford.verdict)}`}>
                {c.afford.label}
              </span>
              <span role="cell" className={`queue__out ${verdictClass(c.verdict)}`}>
                {shortDecision(c.decision)}
                {c.conflicts.length > 0 && (
                  <span className="queue__flag" title={`${c.conflicts.length} conflict(s) found`}>
                    ⚑
                  </span>
                )}
              </span>
            </button>
          ))}
        </div>
      </div>
    </>
  )
}

function Legend({ color, label }: { color: string; label: string }) {
  return (
    <span className="planelegend__item">
      <span
        className="planelegend__swatch"
        style={{
          background: `color-mix(in srgb, ${color} 16%, transparent)`,
          borderColor: `color-mix(in srgb, ${color} 55%, transparent)`,
        }}
      />
      {label}
    </span>
  )
}

function Stat({ label, value, cls }: { label: string; value: string; cls: string }) {
  return (
    <div>
      <div className="eyebrow">{label}</div>
      <div className={`figure planeread__stat ${cls}`}>{value}</div>
    </div>
  )
}
