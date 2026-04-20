declare global {
  interface Window {
    __CDP_CONFIG__: {
      apiUrl: string;
      collectorUrl: string;
    };
  }
}

// Config is injected as an inline <script> by layout.tsx (server component),
// which reads API_URL / COLLECTOR_URL from env at request time.
export function getConfig() {
  if (typeof window !== "undefined" && window.__CDP_CONFIG__) {
    return window.__CDP_CONFIG__;
  }
  return { apiUrl: "", collectorUrl: "" };
}
