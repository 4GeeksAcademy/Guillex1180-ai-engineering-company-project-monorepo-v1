import { useMemo, useState } from "react";
import axios from "axios";
import { AnalysisSummary } from "../components/AnalysisSummary";
import { BreakdownTable } from "../components/BreakdownTable";
import { CsvUpload } from "../components/CsvUpload";
import { ExportResultsButton } from "../components/ExportResultsButton";
import { analyzeIncidents, exportIncidentResults } from "../services/incidentsApi";
import type { IncidentAnalysisResult } from "../types/incidents";

type UiState = "idle" | "selected" | "analyzing" | "completed" | "error";

function toHumanStatus(statusCode: string): string {
  const map: Record<string, string> = {
    OPEN: "OPEN",
    CLOSED: "CLOSED",
    DISCARDED: "DISCARDED",
  };
  return map[statusCode] ?? statusCode;
}

export function IncidentAnalysisPage() {
  const [file, setFile] = useState<File | null>(null);
  const [uiState, setUiState] = useState<UiState>("idle");
  const [result, setResult] = useState<IncidentAnalysisResult | null>(null);
  const [errorMessage, setErrorMessage] = useState<string | null>(null);
  const [isDownloading, setIsDownloading] = useState(false);

  const statusMessage = useMemo(() => {
    if (uiState === "analyzing") {
      return "Analizando incidencias...";
    }
    if (uiState === "completed") {
      return "Análisis completado.";
    }
    if (uiState === "error") {
      return "No se pudo completar el análisis.";
    }
    if (file) {
      return "Archivo seleccionado. Listo para analizar.";
    }
    return "Sin archivo seleccionado.";
  }, [uiState, file]);

  const handleAnalyze = async () => {
    if (!file || uiState === "analyzing") {
      return;
    }

    setUiState("analyzing");
    setErrorMessage(null);

    try {
      const analysisResult = await analyzeIncidents(file);
      setResult(analysisResult);
      setUiState("completed");
    } catch (error) {
      const fallback = "No se pudo conectar con el backend.";
      if (axios.isAxiosError<{ detail?: string }>(error)) {
        setErrorMessage(error.response?.data?.detail ?? fallback);
      } else {
        setErrorMessage(fallback);
      }
      setUiState("error");
    }
  };

  const handleDownload = async () => {
    setIsDownloading(true);
    setErrorMessage(null);

    try {
      const exported = await exportIncidentResults();
      const url = URL.createObjectURL(exported.blob);
      const anchor = document.createElement("a");
      anchor.href = url;
      anchor.download = exported.fileName;
      document.body.appendChild(anchor);
      anchor.click();
      anchor.remove();
      URL.revokeObjectURL(url);
    } catch (error) {
      const fallback = "No se pudieron exportar los resultados.";
      if (axios.isAxiosError<{ detail?: string }>(error)) {
        setErrorMessage(error.response?.data?.detail ?? fallback);
      } else {
        setErrorMessage(fallback);
      }
    } finally {
      setIsDownloading(false);
    }
  };

  const statusBreakdown = useMemo(() => {
    if (!result) {
      return {};
    }

    return Object.fromEntries(
      Object.entries(result.by_status).map(([key, value]) => [toHumanStatus(key), value]),
    );
  }, [result]);

  return (
    <div className="page-shell">
      <header className="page-header">
        <h1>Análisis de incidencias</h1>
        <p>
          Carga un CSV de TrackFlow y analiza volumen, calidad de datos, categorías, estados e índice de satisfacción.
        </p>
      </header>

      <p className="live-region" role="status" aria-live="polite">
        {statusMessage}
      </p>

      <CsvUpload
        file={file}
        disabled={uiState === "analyzing"}
        error={errorMessage}
        onFileSelected={(selected) => {
          setFile(selected);
          setUiState("selected");
          setErrorMessage(null);
        }}
        onInvalidFile={(message) => {
          setFile(null);
          setUiState("error");
          setErrorMessage(message);
        }}
      />

      <div className="actions-row">
        <button type="button" className="action-button" onClick={handleAnalyze} disabled={!file || uiState === "analyzing"}>
          {uiState === "analyzing" ? "Analizando..." : "Ejecutar análisis"}
        </button>
        <ExportResultsButton
          disabled={!result || uiState === "analyzing"}
          loading={isDownloading}
          onDownload={handleDownload}
        />
      </div>

      {result ? (
        <>
          <AnalysisSummary result={result} />

          <section className="panel">
            <h2>Registros inválidos</h2>
            {result.invalid_records > 0 ? (
              <>
                <p className="warning-text">
                  Se detectaron {result.invalid_records} registros inválidos.
                </p>
                <BreakdownTable title="Desglose por tipo de problema" data={result.validation_errors} />
              </>
            ) : (
              <p className="success-text">No se detectaron registros inválidos.</p>
            )}
          </section>

          <BreakdownTable
            title="Incidencias por categoría"
            data={result.by_category}
            showPercentage
            total={result.valid_records}
          />
          <BreakdownTable
            title="Incidencias por estado"
            data={statusBreakdown}
            showPercentage
            total={result.valid_records}
          />

          <section className="panel">
            <h2>Índice de satisfacción</h2>
            {result.average_satisfaction === null ? (
              <p className="helper-text">No hay datos de satisfacción disponibles.</p>
            ) : (
              <p className="satisfaction-score">{result.average_satisfaction.toFixed(2)}</p>
            )}
          </section>

          <section className="panel">
            <h2>Detalle de validaciones</h2>
            {result.validation_error_details.length === 0 ? (
              <p className="helper-text">No hay errores de validación por fila.</p>
            ) : (
              <ul className="details-list">
                {result.validation_error_details.map((detail) => (
                  <li key={detail}>{detail}</li>
                ))}
              </ul>
            )}
          </section>
        </>
      ) : null}
    </div>
  );
}
