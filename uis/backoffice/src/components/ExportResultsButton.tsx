interface ExportResultsButtonProps {
  disabled: boolean;
  loading: boolean;
  onDownload: () => void;
}

export function ExportResultsButton({ disabled, loading, onDownload }: ExportResultsButtonProps) {
  return (
    <button type="button" className="action-button" disabled={disabled || loading} onClick={onDownload}>
      {loading ? "Descargando..." : "Descargar resultados CSV"}
    </button>
  );
}
