import { STATUS_LABELS, ORIGIN_LABELS } from "./constants";
import type { IncidentSummary } from "./types";

interface IncidentDashboardProps {
  summary: IncidentSummary | null;
  isLoading: boolean;
}

function KpiCard({ label, value, color }: { label: string; value: number; color?: string }) {
  return (
    <div className="kpi-card" style={color ? { borderLeftColor: color } : undefined}>
      <p className="kpi-value">{value}</p>
      <p className="kpi-label">{label}</p>
    </div>
  );
}

function Bar({ label, count, total }: { label: string; count: number; total: number }) {
  const pct = total > 0 ? (count / total) * 100 : 0;
  return (
    <div className="bar-row">
      <span className="bar-label">{label}</span>
      <div className="bar-track">
        <div className="bar-fill" style={{ width: `${pct}%` }} />
      </div>
      <span className="bar-count">{count}</span>
    </div>
  );
}

export function IncidentDashboard({ summary, isLoading }: IncidentDashboardProps) {
  if (isLoading) return <section className="dashboard"><p className="text-muted">Cargando métricas…</p></section>;
  if (!summary) return <section className="dashboard"><p className="text-muted">No hay datos disponibles.</p></section>;

  const total = Object.values(summary.by_status).reduce((a, b) => a + b, 0);

  if (total === 0) {
    return (
      <section className="dashboard">
        <p className="text-muted">No hay incidencias registradas. Las métricas aparecerán cuando existan datos.</p>
      </section>
    );
  }

  const byStatus = Object.entries(summary.by_status).filter(([, v]) => v > 0);
  const byCategory = Object.entries(summary.by_category).sort((a, b) => b[1] - a[1]);
  const byOrigin = Object.entries(summary.by_origin).filter(([, v]) => v > 0);
  const byBranch = Object.entries(summary.by_branch).sort((a, b) => b[1] - a[1]);

  return (
    <section className="dashboard">
      <div className="kpi-grid">
        {byStatus.map(([status, count]) => (
          <KpiCard
            key={status}
            label={STATUS_LABELS[status as keyof typeof STATUS_LABELS] ?? status}
            value={count}
          />
        ))}
        <KpiCard label="Total" value={total} />
      </div>

      <div className="dashboard-grid">
        {byCategory.length > 0 && (
          <div className="dashboard-card">
            <h3>Por categoría</h3>
            {byCategory.map(([cat, count]) => (
              <Bar key={cat} label={cat} count={count} total={total} />
            ))}
          </div>
        )}
        {byOrigin.length > 0 && (
          <div className="dashboard-card">
            <h3>Por origen</h3>
            {byOrigin.map(([origin, count]) => (
              <Bar
                key={origin}
                label={ORIGIN_LABELS[origin as keyof typeof ORIGIN_LABELS] ?? origin}
                count={count}
                total={total}
              />
            ))}
          </div>
        )}
        {byBranch.length > 0 && (
          <div className="dashboard-card">
            <h3>Por sede</h3>
            {byBranch.map(([branch, count]) => (
              <Bar key={branch} label={branch} count={count} total={total} />
            ))}
          </div>
        )}
      </div>
    </section>
  );
}