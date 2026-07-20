import { createContext, useCallback, useContext, useEffect, useState, type ReactNode } from 'react'
import { API_URL, BUNDLED, loadDataset, type Dataset } from './source'
import { setActiveDataset } from './store'

interface DataState extends Dataset {
  loading: boolean
  /** re-attempt the live read after a failure */
  retry: () => void
}

const Ctx = createContext<DataState>({ ...BUNDLED, loading: false, retry: () => {} })

export const useData = () => useContext(Ctx)

export function DataProvider({ children }: { children: ReactNode }) {
  // start from the bundle so the workbench renders immediately and never shows
  // a spinner for data it already has in memory
  const [data, setData] = useState<Dataset>(BUNDLED)
  const [loading, setLoading] = useState(Boolean(API_URL))

  const load = useCallback(() => {
    if (!API_URL) return
    setLoading(true)
    loadDataset()
      .then((next) => {
        setActiveDataset(next)
        setData(next)
      })
      .finally(() => setLoading(false))
  }, [])

  useEffect(load, [load])

  return <Ctx.Provider value={{ ...data, loading, retry: load }}>{children}</Ctx.Provider>
}
