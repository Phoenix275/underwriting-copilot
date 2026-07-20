import { useData } from '../data/DataContext'
import { API_URL } from '../data/source'

/** Says where the numbers on screen came from.
 *
 *  A workbench that silently falls back to a stale snapshot when its backend is
 *  unreachable is worse than one that fails loudly — an underwriter would be
 *  reading yesterday's book without knowing. This is always visible. */
export default function SourceBadge() {
  const { source, error, loading, servedAt, retry } = useData()

  if (loading) {
    return (
      <p className="srcbadge srcbadge--wait">
        <span className="srcbadge__dot" />
        Reading the live book…
      </p>
    )
  }

  if (source === 'live') {
    return (
      <p className="srcbadge srcbadge--live" title={servedAt ? `Served ${servedAt}` : undefined}>
        <span className="srcbadge__dot" />
        Live from the API
      </p>
    )
  }

  // configured for live but reading the bundle: that is a fault, not a mode
  if (API_URL) {
    return (
      <div className="srcbadge srcbadge--stale">
        <p>
          <span className="srcbadge__dot" />
          Showing the built-in snapshot
        </p>
        <p className="srcbadge__why">The API did not answer: {error}</p>
        <button type="button" className="srcbadge__retry" onClick={retry}>
          Try again
        </button>
      </div>
    )
  }

  return (
    <p className="srcbadge" title="This build has no API configured">
      <span className="srcbadge__dot" />
      Built-in snapshot
    </p>
  )
}
