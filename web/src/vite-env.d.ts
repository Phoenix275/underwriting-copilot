/// <reference types="vite/client" />

interface ImportMetaEnv {
  /** Base URL of the FastAPI service. Unset builds are read-only snapshots. */
  readonly VITE_API_URL?: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
