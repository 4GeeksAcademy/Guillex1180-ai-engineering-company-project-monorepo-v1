import { STATUS_LABELS, STATUS_COLORS, ORIGIN_LABELS } from "./constants";
import type { Incident, IncidentStatus } from "./types";

interface IncidentTableProps {
  isLoading: boolean;
  incidents: Incident[];
  onStatusChange: (id: number, status: IncidentStatus) => Promise<void>;
}

function formatDate(iso: string): string {
  return new Intl.DateTimeFormat("es-ES", {
    dateStyle: "medium",
    timeStyle: "short",
  }).format(new Date(iso));
}

export function IncidentTable({ isLoading, incidents, onStatusChange }: IncidentTableProps) {
  return (
    <section className="table-frame" aria-busy={isLoading}>
      <div className="table-scroll">
        <table>
          <thead>
            <tr>
              <th>ID</th>
              <th>Título</th>
              <th>Categoría</th>
              <th>Estado</th>
              <th>Origen</th>
              <th>Sede</th>
              <th>Creado</th>
              <th>Acción</th>
            </tr>
          </thead>
          <tbody>
            {incidents.length === 0 ? (
              <tr>
                <td colSpan={8} className="empty-cell">
                  {isLoading ? "Cargando…" : "No hay incidencias registradas."}
                </td>
              </tr>
            ) : (
              incidents.map((inc) => (
                <tr key={inc.id}>
                  <td className="cell-id">{inc.incident_id ?? `#${inc.id}`}</td>
                  <td className="cell-title">
                    <strong>{inc.title}</strong>
                    <p className="cell-desc">{inc.description}</p>
                  </td>
                  <td><span className="badge">{inc.category}</span></td>
                  <td>
                    <span
                      className="status-badge"
                      style={{ "--status-color": STATUS_COLORS[inc.status] } as React.CSSProperties}
                    >
                      {STATUS_LABELS[inc.status]}
                    </span>
                  </td>
                  <td>{ORIGIN_LABELS[inc.origin] ?? inc.origin}</td>
                  <td>{inc.branch}</td>
                  <td className="cell-date">{formatDate(inc.created_at)}</td>
                  <td>
                    <StatusActions incident={inc} onStatusChange={onStatusChange} />
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>
    </section>
  );
}

function StatusActions({
  incident,
  onStatusChange,
}: {
  incident: Incident;
  onStatusChange: (id: number, status: IncidentStatus) => Promise<void>;
}) {
  if (incident.status === "resolved" || incident.status === "discarded") {
    return <span className="text-muted">—</span>;
  }

  const nextOptions: { label: string; status: IncidentStatus }[] = [];
  if (incident.status === "open") {
    nextOptions.push({ label: "Iniciar", status: "in_progress" });
    nextOptions.push({ label: "Descartar", status: "discarded" });
  } else if (incident.status === "in_progress") {
    nextOptions.push({ label: "Resolver", status: "resolved" });
    nextOptions.push({ label: "Descartar", status: "discarded" });
  }

  return (
    <div className="action-group">
      {nextOptions.map((opt) => (
        <button
          key={opt.status}
          className="btn-sm"
          onClick={() => onStatusChange(incident.id, opt.status)}
        >
          {opt.label}
        </button>
      ))}
    </div>
  );
}