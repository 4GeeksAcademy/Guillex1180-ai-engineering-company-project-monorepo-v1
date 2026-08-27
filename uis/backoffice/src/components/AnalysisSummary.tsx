import type { IncidentAnalysisResult } from "../types/incidents";
import { MetricCard } from "./MetricCard";

interface AnalysisSummaryProps {
  result: IncidentAnalysisResult;
}

export function AnalysisSummary({ result }: AnalysisSummaryProps) {
  const hasInvalid = result.invalid_records > 0;

  return (
    <section className="panel">
      <h2>Resumen general</h2>
      <div className="metrics-grid">
        <MetricCard label="Total procesados" value={result.total_processed} />
        <MetricCard label="Registros válidos" value={result.valid_records} tone="positive" />
        <MetricCard label="Registros inválidos" value={result.invalid_records} tone={hasInvalid ? "warning" : "positive"} />
      </div>
    </section>
  );
}
