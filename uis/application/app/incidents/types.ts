/** Tipos para el módulo de Incidencias. */

export type IncidentStatus = "open" | "in_progress" | "resolved" | "discarded";
export type IncidentOrigin = "customer" | "branch" | "internal";

export interface Incident {
  id: number;
  incident_id: string | null;
  title: string;
  description: string;
  category: string;
  status: IncidentStatus;
  origin: IncidentOrigin;
  branch: string;
  created_at: string;
  updated_at: string;
}

export interface IncidentCreate {
  incident_id?: string;
  title: string;
  description: string;
  category: string;
  origin: IncidentOrigin;
  branch: string;
}

export interface IncidentSummary {
  by_status: Record<string, number>;
  by_category: Record<string, number>;
  by_origin: Record<string, number>;
  by_branch: Record<string, number>;
}