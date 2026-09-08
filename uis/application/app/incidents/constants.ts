import type { IncidentOrigin, IncidentStatus } from "./types";

export const STATUS_LABELS: Record<IncidentStatus, string> = {
  open: "Abierto",
  in_progress: "En progreso",
  resolved: "Resuelto",
  discarded: "Descartado",
};

export const STATUS_COLORS: Record<IncidentStatus, string> = {
  open: "var(--status-open)",
  in_progress: "var(--status-progress)",
  resolved: "var(--status-resolved)",
  discarded: "var(--status-discarded)",
};

export const ORIGIN_LABELS: Record<IncidentOrigin, string> = {
  customer: "Cliente",
  branch: "Sede",
  internal: "Interno",
};

export const CATEGORY_OPTIONS = [
  { value: "logistics_damage", label: "Daño logístico" },
  { value: "lost_package", label: "Paquete perdido" },
  { value: "delayed_delivery", label: "Entrega retrasada" },
  { value: "wrong_item", label: "Artículo incorrecto" },
  { value: "it_outage", label: "Fallo de IT" },
  { value: "warehouse_issue", label: "Problema de almacén" },
  { value: "customer_complaint", label: "Reclamo de cliente" },
  { value: "other", label: "Otro" },
] as const;

export const BRANCH_OPTIONS = [
  { value: "Madrid-Centro", label: "Madrid Centro" },
  { value: "Madrid-Getafe", label: "Madrid Getafe" },
  { value: "Barcelona-Sede", label: "Barcelona Sede" },
  { value: "Barcelona-Hospitalet", label: "Barcelona Hospitalet" },
  { value: "Valencia", label: "Valencia" },
  { value: "Sevilla", label: "Sevilla" },
  { value: "Bilbao", label: "Bilbao" },
  { value: "Zaragoza", label: "Zaragoza" },
  { value: "Málaga", label: "Málaga" },
  { value: "central", label: "Central" },
] as const;