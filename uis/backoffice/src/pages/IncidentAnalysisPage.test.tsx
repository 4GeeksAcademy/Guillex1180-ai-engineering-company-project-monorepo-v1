import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { BrowserRouter } from "react-router-dom";
import App from "../App";
import { IncidentAnalysisPage } from "./IncidentAnalysisPage";
import { analyzeIncidents, exportIncidentResults } from "../services/incidentsApi";

vi.mock("../services/incidentsApi", () => ({
  analyzeIncidents: vi.fn(),
  exportIncidentResults: vi.fn(),
}));

const mockedAnalyze = vi.mocked(analyzeIncidents);
const mockedExport = vi.mocked(exportIncidentResults);

const baseResult = {
  total_processed: 100,
  valid_records: 95,
  invalid_records: 5,
  validation_errors: {
    "Tracking inválido": 1,
    "Carrier/país inconsistente": 1,
    "Categoría faltante/inválida": 1,
    "Email faltante/inválido": 1,
    "Cerrado sin satisfacción": 1,
  },
  validation_errors_raw: {
    invalid_tracking_number: 1,
    carrier_country_mismatch: 1,
    invalid_or_missing_category: 1,
    invalid_or_missing_email: 1,
    closed_no_score: 1,
  },
  validation_error_details: ["Fila 5: tracking_number faltante o inválido"],
  by_category: {
    LOST_PARCEL: 14,
    DELAYED_DELIVERY: 38,
    WRONG_ADDRESS: 19,
    RETURN_REQUEST: 17,
    DAMAGE: 7,
  },
  by_status: {
    OPEN: 29,
    CLOSED: 52,
    DISCARDED: 14,
  },
  average_satisfaction: 3.06,
};

beforeEach(() => {
  mockedAnalyze.mockReset();
  mockedExport.mockReset();
});

test("la página aparece en el menú", async () => {
  render(
    <BrowserRouter>
      <App />
    </BrowserRouter>,
  );

  expect(screen.getByRole("link", { name: "Análisis de incidencias" })).toBeInTheDocument();
});

test("permite seleccionar y enviar CSV", async () => {
  const user = userEvent.setup();
  mockedAnalyze.mockResolvedValue(baseResult);

  render(<IncidentAnalysisPage />);

  const fileInput = screen.getByLabelText("Seleccionar archivo CSV") as HTMLInputElement;
  const file = new File(["a,b\n1,2"], "incidents-trackflow.csv", { type: "text/csv" });
  await user.upload(fileInput, file);

  expect(screen.getByText("Archivo seleccionado: incidents-trackflow.csv")).toBeInTheDocument();

  await user.click(screen.getByRole("button", { name: "Ejecutar análisis" }));

  await waitFor(() => {
    expect(mockedAnalyze).toHaveBeenCalledTimes(1);
  });
});

test("muestra estado de carga", async () => {
  const user = userEvent.setup();
  mockedAnalyze.mockImplementation(
    () =>
      new Promise((resolve) => {
        setTimeout(() => resolve(baseResult), 120);
      }),
  );

  render(<IncidentAnalysisPage />);

  const fileInput = screen.getByLabelText("Seleccionar archivo CSV") as HTMLInputElement;
  const file = new File(["a,b\n1,2"], "incidents-trackflow.csv", { type: "text/csv" });
  await user.upload(fileInput, file);
  await user.click(screen.getByRole("button", { name: "Ejecutar análisis" }));

  expect(screen.getByText("Analizando incidencias...")).toBeInTheDocument();
  await waitFor(() => expect(screen.getByText("Análisis completado.")).toBeInTheDocument());
});

test("muestra métricas, categorías, estados, satisfacción e inválidos", async () => {
  const user = userEvent.setup();
  mockedAnalyze.mockResolvedValue(baseResult);

  render(<IncidentAnalysisPage />);

  const fileInput = screen.getByLabelText("Seleccionar archivo CSV") as HTMLInputElement;
  const file = new File(["a,b\n1,2"], "incidents-trackflow.csv", { type: "text/csv" });
  await user.upload(fileInput, file);
  await user.click(screen.getByRole("button", { name: "Ejecutar análisis" }));

  await screen.findByText("Total procesados");
  expect(screen.getByText("95")).toBeInTheDocument();
  expect(screen.getByText("DELAYED_DELIVERY")).toBeInTheDocument();
  expect(screen.getByText("OPEN")).toBeInTheDocument();
  expect(screen.getByText("40.0%")).toBeInTheDocument();
  expect(screen.getByText("3.06")).toBeInTheDocument();
  expect(screen.getByText("Se detectaron 5 registros inválidos.")).toBeInTheDocument();
  expect(screen.getByText("Tracking inválido")).toBeInTheDocument();
});

test("muestra estado positivo sin inválidos", async () => {
  const user = userEvent.setup();
  mockedAnalyze.mockResolvedValue({
    ...baseResult,
    invalid_records: 0,
    validation_errors: {},
    validation_error_details: [],
  });

  render(<IncidentAnalysisPage />);
  const fileInput = screen.getByLabelText("Seleccionar archivo CSV") as HTMLInputElement;
  await user.upload(fileInput, new File(["x"], "incidents-trackflow.csv", { type: "text/csv" }));
  await user.click(screen.getByRole("button", { name: "Ejecutar análisis" }));

  await screen.findByText("No se detectaron registros inválidos.");
});

test("muestra mensaje cuando no hay satisfacción", async () => {
  const user = userEvent.setup();
  mockedAnalyze.mockResolvedValue({
    ...baseResult,
    average_satisfaction: null,
  });

  render(<IncidentAnalysisPage />);
  const fileInput = screen.getByLabelText("Seleccionar archivo CSV") as HTMLInputElement;
  await user.upload(fileInput, new File(["x"], "incidents-trackflow.csv", { type: "text/csv" }));
  await user.click(screen.getByRole("button", { name: "Ejecutar análisis" }));

  await screen.findByText("No hay datos de satisfacción disponibles.");
});

test("deshabilita exportación antes de analizar y permite descargar luego", async () => {
  const user = userEvent.setup();
  mockedAnalyze.mockResolvedValue(baseResult);
  mockedExport.mockResolvedValue({
    fileName: "results.csv",
    blob: new Blob(["metric,value\n"], { type: "text/csv" }),
  });

  if (!URL.createObjectURL) {
    Object.defineProperty(URL, "createObjectURL", {
      writable: true,
      value: () => "blob:mock",
    });
  }
  if (!URL.revokeObjectURL) {
    Object.defineProperty(URL, "revokeObjectURL", {
      writable: true,
      value: () => {},
    });
  }

  const createUrl = vi.spyOn(URL, "createObjectURL").mockReturnValue("blob:mock");
  const revokeUrl = vi.spyOn(URL, "revokeObjectURL").mockImplementation(() => {});

  render(<IncidentAnalysisPage />);

  const exportButton = screen.getByRole("button", { name: "Descargar resultados CSV" });
  expect(exportButton).toBeDisabled();

  const fileInput = screen.getByLabelText("Seleccionar archivo CSV") as HTMLInputElement;
  await user.upload(fileInput, new File(["x"], "incidents-trackflow.csv", { type: "text/csv" }));
  await user.click(screen.getByRole("button", { name: "Ejecutar análisis" }));

  await screen.findByText("Análisis completado.");
  expect(exportButton).toBeEnabled();

  await user.click(exportButton);
  await waitFor(() => expect(mockedExport).toHaveBeenCalledTimes(1));

  createUrl.mockRestore();
  revokeUrl.mockRestore();
});

test("muestra errores del backend", async () => {
  const user = userEvent.setup();
  mockedAnalyze.mockRejectedValue({
    isAxiosError: true,
    response: {
      data: {
        detail: "Faltan columnas obligatorias: status, category.",
      },
    },
  });

  render(<IncidentAnalysisPage />);

  const fileInput = screen.getByLabelText("Seleccionar archivo CSV") as HTMLInputElement;
  await user.upload(fileInput, new File(["x"], "incidents-trackflow.csv", { type: "text/csv" }));
  await user.click(screen.getByRole("button", { name: "Ejecutar análisis" }));

  await screen.findByText("Faltan columnas obligatorias: status, category.");
});

test("muestra error accesible al seleccionar archivo no CSV", async () => {
  render(<IncidentAnalysisPage />);

  const dropzone = screen.getByRole("button", {
    name: "Arrastra y suelta un archivo CSV o haz clic para seleccionarlo",
  });
  const invalidFile = new File(["x"], "incidents-trackflow.txt", { type: "text/plain" });
  fireEvent.drop(dropzone, {
    dataTransfer: { files: [invalidFile] },
  });

  await screen.findByRole("alert");
  expect(screen.getByText("Solo se permiten archivos CSV.")).toBeInTheDocument();
});
