import type { Incident, IncidentCreate, IncidentSummary } from "./types";

const API_BASE = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...options?.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => null);
    const detail = body?.detail;
    const message = Array.isArray(detail)
      ? detail.map((item: { msg?: string }) => item.msg).filter(Boolean).join(" ")
      : detail;
    throw new Error(message || "La API no pudo completar la solicitud.");
  }

  return response.json() as Promise<T>;
}

export function getIncidents(filters?: {
  status?: string;
  origin?: string;
  branch?: string;
  category?: string;
}): Promise<Incident[]> {
  const params = new URLSearchParams();
  if (filters?.status) params.set("status", filters.status);
  if (filters?.origin) params.set("origin", filters.origin);
  if (filters?.branch) params.set("branch", filters.branch);
  if (filters?.category) params.set("category", filters.category);
  const query = params.size ? `?${params.toString()}` : "";
  return request<Incident[]>(`/api/incidents${query}`);
}

export function getIncident(id: number): Promise<Incident> {
  return request<Incident>(`/api/incidents/${id}`);
}

export function createIncident(payload: IncidentCreate): Promise<Incident> {
  return request<Incident>("/api/incidents", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateStatus(id: number, status: string): Promise<Incident> {
  return request<Incident>(`/api/incidents/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}

export function getSummary(): Promise<{
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  by_origin: Record<string, number>;
  by_branch: Record<string, number>;
}> {
  return request("/api/incidents/summary");
}