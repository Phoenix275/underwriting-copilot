import { useCallback, useEffect, useState } from 'react'
import { cases, report } from './data'
import ErrorBoundary from './components/ErrorBoundary'
import Seal from './components/Seal'
import { IconEvidence, IconFile, IconFlow, IconPlane, IconScore } from './components/icons'
import Portfolio from './views/Portfolio'
import CaseFile from './views/CaseFile'
import Pipeline from './views/Pipeline'
import Evidence from './views/Evidence'
import ScoreApplication from './views/ScoreApplication'

export type ViewId = 'portfolio' | 'case' | 'pipeline' | 'evidence' | 'score'

const NAV: { id: ViewId; label: string; short: string; Icon: (p: { className?: string }) => React.ReactElement }[] = [
  { id: 'portfolio', label: 'Portfolio', short: 'Book', Icon: IconPlane },
  { id: 'case', label: 'Case file', short: 'Case', Icon: IconFile },
  { id: 'pipeline', label: 'How it decides', short: 'Flow', Icon: IconFlow },
  { id: 'evidence', label: 'Evidence', short: 'Proof', Icon: IconEvidence },
  { id: 'score', label: 'New application', short: 'Score', Icon: IconScore },
]

export default function App() {
  const [view, setView] = useState<ViewId>('portfolio')
  // open on a case that both needs a human and has a document packet behind it,
  // so the first file anyone reads shows the whole evidence chain
  const [caseId, setCaseId] = useState<string>(
    () => (cases.find((c) => c.referred && c.has_docs) ?? cases[0]).id,
  )

  const selected = cases.find((c) => c.id === caseId) ?? cases[0]

  const openCase = useCallback((id: string) => {
    setCaseId(id)
    setView('case')
  }, [])

  // each view is its own scroll context; moving between them should start at
  // the top the way opening a new document does
  useEffect(() => {
    document.querySelector('.view')?.scrollTo({ top: 0 })
    window.scrollTo({ top: 0 })
  }, [view, caseId])

  const nav = (
    <>
      {NAV.map(({ id, label, Icon }) => (
        <button
          key={id}
          type="button"
          className="rail__link"
          aria-current={view === id ? 'page' : undefined}
          onClick={() => setView(id)}
        >
          <Icon className="rail__icon" />
          <span>{label}</span>
          {id === 'portfolio' && <span className="rail__count figure">{cases.length}</span>}
          {id === 'case' && <span className="rail__count figure">{selected.id.replace('APP-', '')}</span>}
        </button>
      ))}
    </>
  )

  return (
    <div className="shell">
      <header className="rail">
        <div className="rail__mark">
          <Seal size={34} className="rail__seal" spin={90} />
          <div>
            <div className="rail__wordmark">
              Underwriting
              <br />
              Copilot
            </div>
            <div className="rail__sub">Financial viability</div>
          </div>
        </div>

        <nav className="rail__nav" aria-label="Sections">
          {nav}
        </nav>

        <div className="rail__foot">
          <div className="rail__stamp">
            Book of {report.n_applicants.toLocaleString('en-US')}
            <br />
            {cases.length} packets read
            <br />
            Run {report.generated_at}
          </div>
        </div>
      </header>

      <main className="view">
        <ErrorBoundary key={view}>
          {view === 'portfolio' && <Portfolio onOpen={openCase} selectedId={selected.id} />}
          {view === 'case' && <CaseFile c={selected} onOpen={openCase} onGo={setView} />}
          {view === 'pipeline' && <Pipeline c={selected} onGo={setView} />}
          {view === 'evidence' && <Evidence />}
          {view === 'score' && <ScoreApplication seed={selected} />}
        </ErrorBoundary>
      </main>

      <nav className="dock" aria-label="Sections">
        {NAV.map(({ id, short, Icon }) => (
          <button
            key={id}
            type="button"
            className="dock__link"
            aria-current={view === id ? 'page' : undefined}
            onClick={() => setView(id)}
          >
            <Icon className="dock__icon" />
            <span>{short}</span>
          </button>
        ))}
      </nav>
    </div>
  )
}
