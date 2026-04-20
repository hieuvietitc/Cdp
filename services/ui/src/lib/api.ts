import axios from "axios";
import { getConfig } from "./config";

export const api = axios.create();

// Resolve baseURL dynamically at request time (runtime config, not build-time)
api.interceptors.request.use((config) => {
  config.baseURL = getConfig().apiUrl;
  const token = typeof window !== "undefined" ? localStorage.getItem("cdp_token") : null;
  if (token) config.headers.Authorization = `Bearer ${token}`;
  return config;
});

// Auto-redirect to login on 401
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401 && typeof window !== "undefined") {
      localStorage.removeItem("cdp_token");
      window.location.href = "/login";
    }
    return Promise.reject(err);
  }
);

// ── API helpers ────────────────────────────────────────────────────────────

export const profilesApi = {
  list: (params?: Record<string, unknown>) => api.get("/api/v1/profiles", { params }),
  get: (id: string) => api.get(`/api/v1/profiles/${id}`),
  events: (id: string, params?: Record<string, unknown>) => api.get(`/api/v1/profiles/${id}/events`, { params }),
  segments: (id: string) => api.get(`/api/v1/profiles/${id}/segments`),
};

export const segmentsApi = {
  list: () => api.get("/api/v1/segments"),
  get: (id: string) => api.get(`/api/v1/segments/${id}`),
  create: (data: unknown) => api.post("/api/v1/segments", data),
  update: (id: string, data: unknown) => api.put(`/api/v1/segments/${id}`, data),
  delete: (id: string) => api.delete(`/api/v1/segments/${id}`),
  compute: (id: string) => api.post(`/api/v1/segments/${id}/compute`),
  preview: (id: string) => api.get(`/api/v1/segments/${id}/preview`),
  members: (id: string, page = 1) => api.get(`/api/v1/segments/${id}/members`, { params: { page } }),
};

export const activationsApi = {
  list: () => api.get("/api/v1/activations"),
  create: (data: unknown) => api.post("/api/v1/activations", data),
  get: (id: string) => api.get(`/api/v1/activations/${id}`),
  log: (id: string) => api.get(`/api/v1/activations/${id}/log`),
};

export const destinationsApi = {
  list: () => api.get("/api/v1/destinations"),
  create: (data: unknown) => api.post("/api/v1/destinations", data),
  test: (id: string) => api.post(`/api/v1/destinations/${id}/test`),
};

export const analyticsApi = {
  timeseries: (eventType: string, days = 30) =>
    api.get("/api/v1/analytics/events/timeseries", { params: { event_type: eventType, days } }),
  profileGrowth: (days = 90) => api.get("/api/v1/analytics/profiles/growth", { params: { days } }),
  topDestinations: (days = 90) => api.get("/api/v1/analytics/top_destinations", { params: { days } }),
  funnel: (events: string, days = 30) =>
    api.get("/api/v1/analytics/funnel", { params: { events, days } }),
};

export const authApi = {
  login: (email: string, password: string) => api.post("/api/v1/auth/login", { email, password }),
};

export const sourcesApi = {
  list: () => api.get("/api/v1/sources"),
  get: (id: string) => api.get(`/api/v1/sources/${id}`),
  create: (data: { name: string; type: string }) => api.post("/api/v1/sources", data),
  stats: (id: string) => api.get(`/api/v1/sources/${id}/stats`),
  rotateKey: (id: string) => api.post(`/api/v1/sources/${id}/rotate-key`),
};
