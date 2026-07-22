import bundledCases from './cases.json'
import bundledReport from './report.json'
import type { Case, Report } from './types'

/** Where the workbench gets its data.
 *
 *  Two tiers, and the offline one is not a degraded mode — it is the artifact
 *  that ships to Cloudflare Pages, GitHub Pages and a USB stick. When VITE_API_URL is
 *  set the app reads the live book from the FastAPI service instead; if that
 *  call fails for any reason it falls back to the bundle and says so in the
 *  interface rather than showing an empty page.
 *
 *  The evaluation report travels with the cases because it carries the model
 *  coefficients and decision thresholds the browser scores with — reading cases
 *  from one run and thresholds from another would silently mis-score. */

export type DataSource = 'live' | 'bundled'

export interface Dataset {
  cases: Case[]
  report: Report
  source: DataSource
  /** why the live read failed, when it did */
  error?: string
  /** when the API produced this snapshot */
  servedAt?: string
}

export const API_URL: string | undefined =
  (import.meta.env.VITE_API_URL as string | undefined)?.replace(/\/$/, '') || undefined

export const BUNDLED: Dataset = {
  cases: bundledCases as unknown as Case[],
  report: bundledReport as unknown as Report,
  source: 'bundled',
}

/** A live read must not hang the page — the bundle is already in memory, so
 *  waiting more than a few seconds for the network is never the better option. */
const TIMEOUT_MS = 6000

export async function loadDataset(): Promise<Dataset> {
  if (!API_URL) return BUNDLED

  const abort = new AbortController()
  const timer = setTimeout(() => abort.abort(), TIMEOUT_MS)
  try {
    const res = await fetch(`${API_URL}/portfolio`, {
      signal: abort.signal,
      headers: { Accept: 'application/json' },
    })
    if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)

    const body = (await res.json()) as {
      cases: Case[]
      report: Report
      served_at?: string
    }
    if (!Array.isArray(body.cases) || !body.cases.length || !body.report) {
      throw new Error('response did not contain a scored book')
    }

    // the plane's entry order and the case file's prev/next both assume the
    // pipeline's ascending-risk ordering, so sort defensively
    const cases = [...body.cases].sort((a, b) => a.risk_score - b.risk_score)
    return { cases, report: body.report, source: 'live', servedAt: body.served_at }
  } catch (e) {
    const reason =
      e instanceof DOMException && e.name === 'AbortError'
        ? `no response in ${TIMEOUT_MS / 1000}s`
        : e instanceof Error
          ? e.message
          : String(e)
    return { ...BUNDLED, error: reason }
  } finally {
    clearTimeout(timer)
  }
}

/* ---- writes ----------------------------------------------------------- */

export interface DecisionRecord {
  action: 'APPROVED' | 'DECLINED' | 'INFO_REQUESTED'
  rationale: string
  decided_by: string
  decided_at?: string
}

/* Without an API the decision trail lives in the browser: localStorage when the
 * embed allows it, an in-memory map when even that is blocked. The control
 * always works — an underwriter should never meet a dead control with a shell
 * command in it. The trade (local trail is per-browser, not shared) is stated
 * in the panel, not hidden. */
const LS_DECISIONS = 'uwc.decisions'
let memoryTrail: Record<string, DecisionRecord[]> = {}

function readLocalTrail(): Record<string, DecisionRecord[]> {
  try {
    return { ...memoryTrail, ...JSON.parse(localStorage.getItem(LS_DECISIONS) ?? '{}') }
  } catch {
    return memoryTrail
  }
}

function writeLocalTrail(all: Record<string, DecisionRecord[]>) {
  memoryTrail = all
  try {
    localStorage.setItem(LS_DECISIONS, JSON.stringify(all))
  } catch {
    /* private mode / blocked storage — the in-memory copy still serves the session */
  }
}

export async function fetchDecisions(caseId: string): Promise<DecisionRecord[]> {
  if (!API_URL) return readLocalTrail()[caseId] ?? []
  const res = await fetch(`${API_URL}/cases/${encodeURIComponent(caseId)}/decisions`)
  if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
  return res.json()
}

/** Every recorded decision across the whole book, newest first — the admin's
 *  audit feed. Each entry carries the case id it was recorded against. */
export interface DecisionEntry extends DecisionRecord {
  caseId: string
}

export async function fetchAllDecisions(): Promise<DecisionEntry[]> {
  let byCase: Record<string, DecisionRecord[]>
  if (!API_URL) {
    byCase = readLocalTrail()
  } else {
    try {
      const res = await fetch(`${API_URL}/decisions`)
      if (!res.ok) throw new Error(`${res.status} ${res.statusText}`)
      byCase = await res.json()
    } catch {
      // the API is unreachable — fall back to whatever this browser recorded,
      // rather than showing the admin an empty trail
      byCase = readLocalTrail()
    }
  }
  const flat: DecisionEntry[] = []
  for (const [caseId, records] of Object.entries(byCase)) {
    for (const r of records) flat.push({ ...r, caseId })
  }
  // newest first; entries without a stamp sort last
  return flat.sort((a, b) => (b.decided_at ?? '').localeCompare(a.decided_at ?? ''))
}

export async function recordDecision(
  caseId: string,
  d: Omit<DecisionRecord, 'decided_at'>,
): Promise<void> {
  if (!API_URL) {
    const all = readLocalTrail()
    const stamp = new Date().toISOString().slice(0, 16).replace('T', ' ')
    all[caseId] = [...(all[caseId] ?? []), { ...d, decided_at: stamp }]
    writeLocalTrail(all)
    return
  }
  const res = await fetch(`${API_URL}/cases/${encodeURIComponent(caseId)}/decision`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(d),
  })
  if (!res.ok) {
    const detail = await res.text().catch(() => '')
    throw new Error(detail || `${res.status} ${res.statusText}`)
  }
}
