import { useRef } from "react";

interface CsvUploadProps {
  file: File | null;
  disabled: boolean;
  error: string | null;
  onFileSelected: (file: File) => void;
  onInvalidFile: (message: string) => void;
}

export function CsvUpload({ file, disabled, error, onFileSelected, onInvalidFile }: CsvUploadProps) {
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleFile = (selectedFile: File | null) => {
    if (!selectedFile) {
      return;
    }
    if (!selectedFile.name.toLowerCase().endsWith(".csv")) {
      onInvalidFile("Solo se permiten archivos CSV.");
      return;
    }
    onFileSelected(selectedFile);
  };

  return (
    <section className="panel">
      <h2>Archivo CSV</h2>
      <p className="helper-text">Sube el archivo con las incidencias para ejecutar el análisis.</p>

      <label htmlFor="csv-file" className="upload-label">
        Seleccionar archivo CSV
      </label>
      <input
        id="csv-file"
        ref={fileInputRef}
        type="file"
        accept=".csv,text/csv"
        onChange={(event) => handleFile(event.target.files?.[0] ?? null)}
        disabled={disabled}
        aria-invalid={Boolean(error)}
        aria-describedby={error ? "csv-upload-error upload-help" : "upload-help"}
      />

      <button
        type="button"
        className="dropzone"
        onClick={() => fileInputRef.current?.click()}
        onDragOver={(event) => event.preventDefault()}
        onDrop={(event) => {
          event.preventDefault();
          const droppedFile = event.dataTransfer.files?.[0] ?? null;
          handleFile(droppedFile);
        }}
        disabled={disabled}
        aria-describedby="upload-help"
      >
        Arrastra y suelta un archivo CSV o haz clic para seleccionarlo
      </button>

      <p id="upload-help" className="helper-text">
        Solo se aceptan archivos con extensión .csv.
      </p>

      {file ? <p className="file-name">Archivo seleccionado: {file.name}</p> : <p className="file-name">Sin archivo seleccionado</p>}

      {error ? (
        <p id="csv-upload-error" className="error-text" role="alert" aria-live="assertive">
          {error}
        </p>
      ) : null}
    </section>
  );
}
