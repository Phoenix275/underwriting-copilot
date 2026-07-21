import { useMemo, useState } from 'react'
import { useData } from '../data/DataContext'
import { useAuth } from '../auth/AuthContext'
import type { Case } from '../data/types'
import PortfolioPlane from '../components/PortfolioPlane'
import RoutingBoard from '../components/RoutingBoard'
import { FILTERS, matchesFilter, strainScore, type PortfolioFilter } from '../lib/plane'
import { DESK_TAG, difficultyBand, isMine } from '../lib/routing'
import type { Route } from '../lib/router'
import { pct, shortDecision, usdShort, verdictClass, affordClass } from '../lib/format'
import '../styles/plane.css'
import '../styles/queue.css'

export default function Portfolio({
  onOpen,
  selectedId,
  route,
  navigate,
}: {
  onOpen: (id: string) => void
  selectedId: string
  route: Route
  navigate: (r: Partial<Route> & { view: 'portfolio' }) => void
}) {
  const { cases, report } = useData()
  const { persona } = useAuth()
  const t = report.decisioning.thresholds
  const role = persona?.role ?? 'oversight'
  const isManager = role === 'oversight'

  const mine = useMemo(() => cases.filter((c) => isMine(c, role)), [cases, role])

  const applyFilter = (c: Case, f: PortfolioFilter) =>
    f === 'mine' ? isMine(c, role) : matchesFilter(c, f)

  // the filter lives in the URL so "here are the declines" is a link you can
  // paste to a colleague, and the back button steps through what you looked at.
  // an underwriter with no filter set lands on their own referral queue.
  const defaultFilter: PortfolioFilter = 'mine'
  const validFilters = new Set<string>([...FILTERS.map((f) => f.id), 'mine'])
  const filter = (validFilters.has(route.params.filter) ? route.params.filter : defaultFilter) as
    PortfolioFilter
  const setFilter = (f: PortfolioFilter) =>
    navigate({ view: 'portfolio', params: f === defaultFilter ? {} : { filter: f } })

  const [hovered, setHovered] = useState<Case | null>(null)

  const items = useMemo(() => cases.filter((c) => applyFilter(c, filter)), [cases, filter, role])
  const shown = hovered ?? cases.find((c) => c.id === selectedId) ?? cases[0]

  const counts = useMemo(
    () => ({
      green: cases.filter((c) => c.verdict === 'green').length,
      yellow: cases.filter((c) => c.verdict === 'yellow').length,
      red: cases.filter((c) => c.verdict === 'red').length,
    }),
    [cases],
  )

  // filter chips: "my queue" first, then the outcome/quality filters
  const myLabel = isManager ? 'All referrals' : 'My queue'
  const chips: { id: PortfolioFilter; label: string; n: number }[] = [
    { id: 'mine', label: myLabel, n: mine.length },
    ...FILTERS.map((f) => ({
      id: f.id,
      label: f.label,
      n: f.id === 'all' ? cases.length : cases.filter((c) => matchesFilter(c, f.id)).length,
    })),
  ]

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

        {/* the manager sees how the referral queue is split across the desks */}
        {isManager && <RoutingBoard onFilterDesk={() => setFilter('mine')} />}

        <div className="srule">
          <span className="eyebrow">
            {filter === 'mine' ? (isManager ? 'The referral queue' : `${persona?.name} · referral queue`) : 'The queue'}
          </span>
        </div>

        {!isManager && (
          <p className="queue__intro">
            You are on the <b>{persona?.title.toLowerCase()}</b> desk. Your queue is the{' '}
            {mine.length} manual-review case{mine.length === 1 ? '' : 's'} routed to you by
            difficulty — the workbench matches each referral to the right level of underwriter, so
            you see the {role === 'senior' ? 'hardest' : role === 'analyst' ? 'most routine' : 'mid-complexity'}{' '}
            files. Switch filters to see the rest of the book.
          </p>
        )}

        <div className="queue__filters" role="group" aria-label="Filter the queue">
          {chips.map((f) => (
            <button
              key={f.id}
              type="button"
              className={`chip${f.id === 'mine' ? ' chip--mine' : ''}`}
              aria-pressed={filter === f.id}
              onClick={() => setFilter(f.id)}
            >
              {f.label}
              <span className="chip__n figure">{f.n}</span>
            </button>
          ))}
        </div>

        <p className="queue__summary">
          {counts.green} approve · {counts.yellow} refer · {counts.red} decline across{' '}
          {cases.length} packets. Straight-through rate {pct(t.stp_est, 1)}, measured on a held-out
          half of the book — the {counts.yellow} referrals are routed across three underwriter desks.
        </p>

        <div className="queue queue--routed" role="table" aria-label="Case queue">
          <div className="queue__head" role="row">
            <span role="columnheader">Applicant</span>
            <span role="columnheader" className="queue__num">Risk</span>
            <span role="columnheader" className="queue__num">Strain</span>
            <span role="columnheader">Outcome</span>
            <span role="columnheader">Assigned · difficulty</span>
          </div>
          {items.map((c) => {
            const band = difficultyBand(c.difficulty)
            return (
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
                  <span className="queue__id figure">
                    {c.id} · {usdShort(c.coverage)}
                  </span>
                </span>
                <span role="cell" className={`figure queue__num ${verdictClass(c.verdict)}`}>
                  {c.risk_score}
                </span>
                <span role="cell" className={`figure queue__num ${affordClass(c.afford.verdict)}`}>
                  {Math.round(strainScore(c))}
                </span>
                <span role="cell" className={`queue__out ${verdictClass(c.verdict)}`}>
                  {shortDecision(c.decision)}
                  {c.conflicts.length > 0 && (
                    <span className="queue__flag" title={`${c.conflicts.length} conflict(s) found`}>
                      ⚑
                    </span>
                  )}
                </span>
                <span role="cell" className="queue__desk">
                  {c.assigned_desk ? (
                    <>
                      <span className={`queue__deskn desk-${c.assigned_desk}`}>
                        {DESK_TAG[c.assigned_desk]}
                      </span>
                      <span className="queue__diff figure" title={band ?? ''}>
                        {c.difficulty}
                      </span>
                    </>
                  ) : (
                    <span className="queue__auto">auto</span>
                  )}
                </span>
              </button>
            )
          })}
          {items.length === 0 && (
            <p className="queue__empty">
              Nothing here right now. Your queue fills as referrals are routed to your desk.
            </p>
          )}
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
