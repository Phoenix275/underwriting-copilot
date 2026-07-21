import { useMemo } from 'react'
import { useData } from '../data/DataContext'
import { DESK_LABEL } from '../lib/routing'
import type { Desk } from '../data/types'

/** The manager's view of the referral queue: how the manual-review cases split
 *  across the three underwriter desks, and how hard each desk's pile is. Only
 *  shown to the oversight persona — this is the "different depending on who
 *  logs in" made concrete. */
export default function RoutingBoard({ onFilterDesk }: { onFilterDesk: (d: Desk) => void }) {
  const { cases, report } = useData()

  // prefer the whole-book routing summary from the report; fall back to the
  // cases actually loaded so it still reads right on the bundled sample
  const board = useMemo(() => {
    const referred = cases.filter((c) => c.referred)
    const desks: Desk[] = ['senior', 'review', 'analyst']
    return desks.map((desk) => {
      const mine = referred.filter((c) => c.assigned_desk === desk)
      const diffs = mine.map((c) => c.difficulty ?? 0)
      const avg = diffs.length ? Math.round(diffs.reduce((a, b) => a + b, 0) / diffs.length) : 0
      return { desk, n: mine.length, avg }
    })
  }, [cases])

  const totalReferred = report.routing?.n_referred ?? cases.filter((c) => c.referred).length

  return (
    <>
      <div className="srule">
        <span className="eyebrow">Referral routing · manager view</span>
      </div>

      <p className="queue__intro">
        {totalReferred.toLocaleString('en-US')} of the book&rsquo;s applications need a human. The
        workbench scores each one for difficulty and routes it to the right desk — the hardest files
        to the senior underwriter, the routine ones to the new analyst — so no one works above or
        below their level. Here is how today&rsquo;s queue is split.
      </p>

      <div className="routing">
        {board.map(({ desk, n, avg }) => (
          <button key={desk} type="button" className="deskcard" onClick={() => onFilterDesk(desk)}>
            <span className={`deskcard__tag desk-${desk}`}>{DESK_LABEL[desk]}</span>
            <span className="figure deskcard__n">{n}</span>
            <span className="deskcard__label">case{n === 1 ? '' : 's'} in queue</span>
            <span className="deskcard__avg">
              avg difficulty <span className="figure">{avg}</span>
            </span>
          </button>
        ))}
      </div>
    </>
  )
}
