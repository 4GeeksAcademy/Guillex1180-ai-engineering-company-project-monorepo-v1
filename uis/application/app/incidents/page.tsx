import { useEffect, useState } from "react";
import { getIncidents, getSummary, createIncident, updateStatus } from "./api";
import { ORIGIN_LABELS } from "./constants";
import { IncidentForm } from "./IncidentForm";
import { IncidentTable } from "./IncidentTable";
import { IncidentDashboard } from "./IncidentDashboard";
import type {
  Incident,
  IncidentCreate,
  IncidentStatus,
  IncidentSummary,
} from "./types";

function errorMessage(error: unknown, fallback: string): string {
  return error instanceof Error ? error.message : fallback;
}

export default function IncidentsPage() {
  const [incidents, setIncidents] = useState<Incident[]>([]);
  const [summary, setSummary] = useState<IncidentSummary | null>(null);
  const [filterOrigin, setFilterOrigin] = useState("");
  const [filterStatus, setFilterStatus] = useState("");
  const [reload, setReload] = useState(0);
  const [isLoading, setIsLoading] = useState(true);
  const [isSaving, setIsSaving] = useState(false);
  const [pendingId, setPendingId] = useState<number | null>(null);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    setIsLoading(true);
    setError(null);

    Promise.all([
      getIncidents({
        status: filterStatus || undefined,
        origin: filterOrigin || undefined,
      }),
      getSummary(),
    ])
      .then(([items, metrics]) => {
        if (!active) return;
        setIncidents(items);
        setSummary(metrics);
      })
      .catch((requestError: unknown) => {
        if (active) setError(errorMessage(requestError, "No se pudo cargar las incidencias."));
      })
      .finally(() => {
        if (active) setIsLoading(false);
      });

    return () => {
      active = false;
    };
  }, [filterOrigin, filterStatus, reload]);

  const handleCreate = async (payload: IncidentCreate) => {
    setIsSaving(true);
    setError(null);
    try {
      await createIncident(payload);
      setReload((value) => value + 1);
    } catch (requestError) {
      setError(errorMessage(requestError, "No se pudo registrar la incidencia."));
    } finally {
      setIsSaving(false);
    }
  };

  const handleStatusChange = async (id: number, status: IncidentStatus) => {
    setPendingId(id);
    setError(null);
    try {
      const updated = await updateStatus(id, status);
      setIncidents((current) =>
        current.map((item) => (item.id === updated.id ? updated : item)),
      );
      getSummary()
        .then(setSummary)
        .catch(() => {});
    } catch (requestError) {
      setError(errorMessage(requestError, "No se pudo actualizar el estado."));
    } finally {
      setPendingId(null);
    }
  };

  return (
    <main className="page">
      <header className="page-header">
        <div>
          <h1>Incidencias</h1>
          <p className="page-subtitle">
            Gestión centralizada de incidencias reportadas por clientes, sedes o internos.
          </p>
        </div>
      </header>

      {error ? (
        <p className="inline-alert" role="alert">{error}</p>
      ) : null}

      <IncidentDashboard summary={summary} isLoading={isLoading} />

      <section className="panel">
        <h2>Registrar nueva incidencia</h2>
        <IncidentForm onSave={handleCreate} isSaving={isSaving} />
      </section>

      <section className="panel">
        <div className="panel-header">
          <h2>Listado de incidencias</h2>
          <div className="filter-bar">
            <label className="filter-item">
              <span>Estado</span>
              <select
                value={filterStatus}
                onChange={(e) => setFilterStatus(e.target.value)}
              >
                <option value="">Todos</option>
                <option value="open">Abierto</option>
                <option value="in_progress">En progreso</option>
                <option value="resolved">Resuelto</option>
                <option value="discarded">Descartado</option>
              </select>
            </label>
            <label className="filter-item">
              <span>Origen</span>
              <select
                value={filterOrigin}
                onChange={(e) => setFilterOrigin(e.target.value)}
              >
                <option value="">Todos</option>
                {Object.entries(ORIGIN_LABELS).map(([val, label]) => (
                  <option key={val} value={val}>{label}</option>
                ))}
              </select>
            </label>
          </div>
        </div>
        <IncidentTable
          isLoading={isLoading}
          incidents={incidents}
          onStatusChange={handleStatusChange}
        />
      </section>
    </main>
  );
}