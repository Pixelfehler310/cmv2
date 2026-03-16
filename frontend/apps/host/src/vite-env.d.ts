/// <reference types="vite/client" />

interface ImportMetaEnv {
  readonly VITE_USE_MOCKS: string;
  readonly VITE_LOG_LEVEL: string;
  readonly VITE_FRONTEND_TESTING_PLAYER_ACTION_LAB?: string;
  // more env variables...
}

interface ImportMeta {
  readonly env: ImportMetaEnv;
}
