import { useCallback, useEffect, useState } from 'react'

/** Hash routing, deliberately — with a memory-mode fallback.
 *
 *  The workbench is served four ways: Cloudflare Pages, a dev server, straight
 *  off disk, and inlined into a page via srcdoc. The first three have a
 *  real URL, so routes live in the hash and are shareable links. Inside a
 *  srcdoc iframe the document's URL is `about:srcdoc`, and Chrome throws a
 *  SecurityError on any history.replaceState / location.hash write there —
 *  which, uncaught, unmounts the whole React tree (the "black screen after
 *  sign-in" bug inside a sandboxed srcdoc iframe). So: if the document has no
 *  real URL,
 *  routing runs in memory instead. Same API, no shareable links (there is no
 *  URL bar inside an iframe to share anyway), and back/forward simply don't
 *  apply.
 *
 *  Hand-rolled rather than pulled from a router package: five static routes and
 *  one parameter do not justify a dependency in a bundle that gets inlined
 *  whole — and no package would have handled about:srcdoc for us either. */

export type ViewId = 'portfolio' | 'case' | 'pipeline' | 'evidence' | 'score'

export interface Route {
  view: ViewId
  /** case id, when the route carries one */
  id?: string
  /** query params after the path, e.g. #/portfolio?filter=red */
  params: Record<string, string>
}

const VIEWS: ViewId[] = ['portfolio', 'case', 'pipeline', 'evidence', 'score']

/** Can this document carry state in its URL? A srcdoc iframe (about:srcdoc) cannot. */
const HAS_URL = (() => {
  try {
    return ['http:', 'https:', 'file:'].includes(window.location.protocol)
  } catch {
    return false
  }
})()

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

/* ---- memory mode ------------------------------------------------------- */

let memoryRoute: Route = { view: 'portfolio', params: {} }
const listeners = new Set<() => void>()

function setMemoryRoute(r: Route) {
  memoryRoute = r
  listeners.forEach((fn) => fn())
}

/* ------------------------------------------------------------------------ */

export function useRoute(): [Route, (r: Partial<Route> & { view: ViewId }) => void] {
  const [route, setRoute] = useState<Route>(() =>
    HAS_URL ? parseHash(window.location.hash) : memoryRoute,
  )

  useEffect(() => {
    if (HAS_URL) {
      const onChange = () => setRoute(parseHash(window.location.hash))
      window.addEventListener('hashchange', onChange)
      // an empty hash on first load should become a real, shareable URL without
      // adding a history entry the user then has to press back through
      if (!window.location.hash) {
        try {
          window.history.replaceState(null, '', buildHash({ view: 'portfolio' }))
        } catch {
          /* some embeds allow reading the URL but not writing it */
        }
      }
      return () => window.removeEventListener('hashchange', onChange)
    }
    const onChange = () => setRoute(memoryRoute)
    listeners.add(onChange)
    return () => {
      listeners.delete(onChange)
    }
  }, [])

  // internal anchors (href="#/…") exist so open-in-new-tab works where there is
  // a real URL. In memory mode their default action would navigate the srcdoc
  // frame itself to about:blank — intercept every one of them.
  useEffect(() => {
    const onClick = (e: MouseEvent) => {
      if (e.defaultPrevented || e.metaKey || e.ctrlKey || e.shiftKey || e.button !== 0) return
      const a = (e.target as Element).closest?.('a[href^="#/"]')
      if (!a) return
      e.preventDefault()
      const next = parseHash(a.getAttribute('href') ?? '')
      if (HAS_URL) {
        window.location.hash = buildHash(next)
      } else {
        setMemoryRoute(next)
      }
    }
    document.addEventListener('click', onClick)
    return () => document.removeEventListener('click', onClick)
  }, [])

  const navigate = useCallback((r: Partial<Route> & { view: ViewId }) => {
    const next = buildHash(r)
    if (HAS_URL) {
      if (next === window.location.hash) return
      // assigning the hash pushes a history entry, so back returns to the
      // previous case rather than leaving the app
      window.location.hash = next
    } else {
      setMemoryRoute(parseHash(next))
    }
  }, [])

  return [route, navigate]
}
