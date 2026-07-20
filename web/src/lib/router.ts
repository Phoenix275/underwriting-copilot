import { useCallback, useEffect, useState } from 'react'

/** Hash routing, deliberately.
 *
 *  The workbench is served three ways — GitHub Pages, a Streamlit iframe, and
 *  straight off disk — and only one of those can be configured to rewrite
 *  unknown paths to index.html. A hash route resolves identically in all three,
 *  including `file://`, where the History API cannot push state at all.
 *
 *  Hand-rolled rather than pulled from a router package: five static routes and
 *  one parameter do not justify a dependency in a bundle that gets inlined
 *  whole, and this way back/forward and link-sharing behave the same offline. */

export type ViewId = 'portfolio' | 'case' | 'pipeline' | 'evidence' | 'score'

export interface Route {
  view: ViewId
  /** case id, when the route carries one */
  id?: string
  /** query params after the path, e.g. #/portfolio?filter=red */
  params: Record<string, string>
}

const VIEWS: ViewId[] = ['portfolio', 'case', 'pipeline', 'evidence', 'score']

export function parseHash(hash: string): Route {
  const raw = hash.replace(/^#\/?/, '')
  const [path, query = ''] = raw.split('?')
  const [head, tail] = path.split('/')

  const params: Record<string, string> = {}
  for (const [k, v] of new URLSearchParams(query)) params[k] = v

  const view = VIEWS.includes(head as ViewId) ? (head as ViewId) : 'portfolio'
  return { view, id: tail ? decodeURIComponent(tail) : undefined, params }
}

export function buildHash(route: Partial<Route> & { view: ViewId }): string {
  const { view, id, params } = route
  const query = new URLSearchParams(params ?? {}).toString()
  return `#/${view}${id ? `/${encodeURIComponent(id)}` : ''}${query ? `?${query}` : ''}`
}

export function useRoute(): [Route, (r: Partial<Route> & { view: ViewId }) => void] {
  const [route, setRoute] = useState<Route>(() => parseHash(window.location.hash))

  useEffect(() => {
    const onChange = () => setRoute(parseHash(window.location.hash))
    window.addEventListener('hashchange', onChange)
    // an empty hash on first load should become a real, shareable URL without
    // adding a history entry the user then has to press back through
    if (!window.location.hash) {
      window.history.replaceState(null, '', buildHash({ view: 'portfolio' }))
    }
    return () => window.removeEventListener('hashchange', onChange)
  }, [])

  const navigate = useCallback((r: Partial<Route> & { view: ViewId }) => {
    const next = buildHash(r)
    if (next === window.location.hash) return
    // assigning the hash pushes a history entry, so back returns to the
    // previous case rather than leaving the app
    window.location.hash = next
  }, [])

  return [route, navigate]
}
