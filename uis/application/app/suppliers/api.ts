import type {
  Supplier,
  SupplierCreate,
  SupplierFilters,
  SupplierStatus,
} from "./types";

const API_BASE_URL = (import.meta.env.VITE_API_BASE_URL ?? "").replace(/\/$/, "");

async function request<T>(path: string, options?: RequestInit): Promise<T> {
  const response = await fetch(`${API_BASE_URL}${path}`, {
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

export function getSuppliers(filters: SupplierFilters = {}): Promise<Supplier[]> {
  const params = new URLSearchParams();
  if (filters.country) params.set("country", filters.country);
  if (filters.category) params.set("category", filters.category);
  const query = params.size ? `?${params.toString()}` : "";
  return request<Supplier[]>(`/suppliers${query}`);
}

export function createSupplier(payload: SupplierCreate): Promise<Supplier> {
  return request<Supplier>("/suppliers", {
    method: "POST",
    body: JSON.stringify(payload),
  });
}

export function updateSupplierRate(id: number, rate: number): Promise<Supplier> {
  return request<Supplier>(`/suppliers/${id}/rate`, {
    method: "PATCH",
    body: JSON.stringify({ rate_per_shipment: rate }),
  });
}

export function updateSupplierStatus(
  id: number,
  status: SupplierStatus,
): Promise<Supplier> {
  return request<Supplier>(`/suppliers/${id}/status`, {
    method: "PATCH",
    body: JSON.stringify({ status }),
  });
}