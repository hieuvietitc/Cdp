declare global {
  interface Window {
    __CDP_CONFIG__?: {
      apiUrl: string;
      collectorUrl: string;
    };
  }
}

const DEFAULTS = {
  apiUrl: "http://localhost:4002",
  collectorUrl: "http://localhost:4001",
};

export function getConfig() {
  if (typeof window !== "undefined" && window.__CDP_CONFIG__) {
    return window.__CDP_CONFIG__;
  }
  return DEFAULTS;
}
