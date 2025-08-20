/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_API_URL: string
  readonly VITE_API_BASE_URL: string
  readonly VITE_ENABLE_DASHBOARD_AI: string
  readonly VITE_API_BASE: string
  readonly VITE_OPENAI_API_KEY: string
}

interface ImportMeta {
  readonly env: ImportMetaEnv
}
