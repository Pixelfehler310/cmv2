const host = typeof window !== "undefined" ? window.location.host : "localhost:3000";
const wsProtocol = typeof window !== "undefined" && window.location.protocol === "https:" ? "wss:" : "ws:";

export const config = {
  useMocks: (import.meta as any).env.VITE_USE_MOCKS === "true",
  apiUrl: (import.meta as any).env.VITE_API_URL || "/api",
  wsUrl: (import.meta as any).env.VITE_WS_URL || `${wsProtocol}//${host}/ws`,
  frontendTesting: {
    playerActionLab: (import.meta as any).env.VITE_FRONTEND_TESTING_PLAYER_ACTION_LAB === "true",
  },
};
