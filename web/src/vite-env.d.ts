/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_BASE_URL: string
  readonly VITE_WS_BASE_URL: string
  readonly VITE_APP_TITLE: string
  readonly VITE_APP_VERSION: string
  readonly VITE_APP_ENV: string
  readonly VITE_ENABLE_REALTIME: string
  readonly VITE_ENABLE_ANALYTICS: string
  readonly VITE_ENABLE_WORKFLOW_EDITOR: string
  readonly VITE_API_TIMEOUT: string
  readonly VITE_WS_RECONNECT_INTERVAL: string
  readonly VITE_WS_MAX_RECONNECT_ATTEMPTS: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}