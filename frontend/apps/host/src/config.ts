export const config = {
  useMocks: (import.meta as any).env.VITE_USE_MOCKS === 'true',
  apiUrl: (import.meta as any).env.VITE_API_URL || '/api',
  wsUrl: (import.meta as any).env.VITE_WS_URL || 'ws://localhost:8000',
};
