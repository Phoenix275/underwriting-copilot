import { useCallback, useEffect, useMemo, useRef, useState } from 'react'
import { DataProvider, useData } from './data/DataContext'
import { useAuth } from './auth/AuthContext'
import SignIn from './auth/SignIn'
import ErrorBoundary from './components/ErrorBoundary'
import RoleBadge from './components/RoleBadge'
import Seal from './components/Seal'
import SourceBadge from './components/SourceBadge'
import { IconEvidence, IconFile, IconFlow, IconPlane, IconScore } from './components/icons'
import { useRoute, type ViewId } from './lib/router'
import Portfolio from './views/Portfolio'
import CaseFile from './views/CaseFile'
import Pipeline from './views/Pipeline'
import Evidence from './views/Evidence'
import ScoreApplication from './views/ScoreApplication'

export type { ViewId }

const NAV: {
  id: ViewId
  label: string
  short: string
  Icon: (p: { className?: string }) => React.ReactElement
}[] = [
  { id: 'portfolio', label: 'Portfolio', short: 'Book', Icon: IconPlane },
  { id: 'case', label: 'Case file', short: 'Case', Icon: IconFile },
  { id: 'pipeline', label: 'How it decides', short: 'Flow', Icon: IconFlow },
  { id: 'evidence', label: 'Evidence', short: 'Proof', Icon: IconEvidence },
  { id: 'score', label: 'New application', short: 'Score', Icon: IconScore },
]

export default function App() {
  const { persona } = useAuth()
  // the sign-in gate is presentation only — it names the underwriter recording
  // decisions, it is not a security boundary
  if (!persona) return <SignIn />
  return (
    <DataProvider>
      <Workbench />
    </DataProvider>
  )
}

function Workbench() {
  const { cases, report } = useData()
  const [route, navigate] = useRoute()
  const view = route.view

  // opening straight onto a case that both needs a human and has a document
  // packet means the first file anyone reads shows the whole evidence chain
  const defaultCase = useMemo(
    () => (cases.find((c) => c.referred && c.has_docs) ?? cases[0]).id,
    [cases],
  )

  // remember the last case opened, so the nav item returns to it rather than
  // resetting every time you leave the view
  const [lastCase, setLastCase] = useState(defaultCase)
  useEffect(() => {
    if (route.view === 'case' && route.id && cases.some((c) => c.id === route.id)) {
      setLastCase(route.id)
    }
  }, [route.view, route.id, cases])

  const selected = cases.find((c) => c.id === route.id) ?? cases.find((c) => c.id === lastCase) ?? cases[0]

  const openCase = useCallback(
    (id: string) => navigate({ view: 'case', id }),
    [navigate],
  )

  const go = useCallback(
    (v: ViewId) => navigate(v === 'case' ? { view: 'case', id: lastCase } : { view: v }),
    [navigate, lastCase],
  )

  // each view is its own document; moving between them should start at the top
  const scroller = useRef<HTMLElement>(null)
  useEffect(() => {
    scroller.current?.scrollTo({ top: 0 })
    window.scrollTo({ top: 0 })
  }, [view, route.id])

  return (
    <div className="shell">
      <header className="rail">
        <a className="rail__mark" href="#/portfolio" aria-label="Underwriting Copilot, portfolio">
          <Seal size={34} className="rail__seal" spin={90} />
          <div>
            <div className="rail__wordmark">
              Underwriting
              <br />
              Copilot
            </div>
            <div className="rail__sub">Financial viability</div>
          </div>
        </a>

        <nav className="rail__nav" aria-label="Sections">
          {NAV.map(({ id, label, Icon }) => (
            <a
              key={id}
              className="rail__link"
              href={id === 'case' ? `#/case/${lastCase}` : `#/${id}`}
              aria-current={view === id ? 'page' : undefined}
            >
              <Icon className="rail__icon" />
              <span>{label}</span>
              {id === 'portfolio' && <span className="rail__count figure">{cases.length}</span>}
              {id === 'case' && (
                <span className="rail__count figure">{selected.id.replace('APP-', '')}</span>
              )}
            </a>
          ))}
        </nav>

        <div className="rail__foot">
          <RoleBadge />
          <SourceBadge />
          <div className="rail__stamp">
            Book of {report.n_applicants.toLocaleString('en-US')}
            <br />
            {cases.length} packets read
            <br />
            Run {report.generated_at}
          </div>
        </div>
      </header>

      <main className="view" ref={scroller}>
        <ErrorBoundary key={view}>
          {view === 'portfolio' && (
            <Portfolio onOpen={openCase} selectedId={selected.id} route={route} navigate={navigate} />
          )}
          {view === 'case' && <CaseFile c={selected} onOpen={openCase} onGo={go} />}
          {view === 'pipeline' && <Pipeline c={selected} onGo={go} />}
          {view === 'evidence' && <Evidence />}
          {view === 'score' && <ScoreApplication />}
        </ErrorBoundary>
      </main>

      <nav className="dock" aria-label="Sections">
        {NAV.map(({ id, short, Icon }) => (
          <a
            key={id}
            className="dock__link"
            href={id === 'case' ? `#/case/${lastCase}` : `#/${id}`}
            aria-current={view === id ? 'page' : undefined}
          >
            <Icon className="dock__icon" />
            <span>{short}</span>
          </a>
        ))}
      </nav>
    </div>
  )
}
