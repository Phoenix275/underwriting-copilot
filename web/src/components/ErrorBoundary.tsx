import { Component, type ErrorInfo, type ReactNode } from 'react'

/** A view that fails should say what failed and leave the rest of the
 *  workbench usable, rather than blanking the page. */
export default class ErrorBoundary extends Component<
  { children: ReactNode },
  { error: Error | null }
> {
  state = { error: null as Error | null }

  static getDerivedStateFromError(error: Error) {
    return { error }
  }

  componentDidCatch(error: Error, info: ErrorInfo) {
    console.error('View failed:', error, info.componentStack)
  }

  render() {
    const { error } = this.state
    if (!error) return this.props.children
    return (
      <div className="viewbody">
        <div className="panel">
          <div className="panel__head">
            <h2 className="panel__title">This view did not load</h2>
          </div>
          <div className="panel__body">
            <p className="sectionlede">
              The rest of the workbench still works — pick another section from the navigation.
            </p>
            <pre className="figure crash">{error.message}</pre>
          </div>
        </div>
      </div>
    )
  }
}
