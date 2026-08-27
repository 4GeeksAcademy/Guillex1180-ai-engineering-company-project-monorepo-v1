import type { ExportedResult, IncidentAnalysisResult } from "../types/incidents";
import { apiClient } from "../lib/apiClient";

export async function analyzeIncidents(file: File): Promise<IncidentAnalysisResult> {
  const formData = new FormData();
  formData.append("file", file);

  const response = await apiClient.post<IncidentAnalysisResult>("/api/incidents/analyze", formData, {
    headers: {
      "Content-Type": "multipart/form-data",
    },
  });

  return response.data;
}

function extractFileName(contentDisposition: string | undefined): string {
  if (!contentDisposition) {
    return "results.csv";
  }

  const match = contentDisposition.match(/filename="?([^";]+)"?/i);
  return match?.[1] ?? "results.csv";
}

export async function exportIncidentResults(): Promise<ExportedResult> {
  const response = await apiClient.get("/api/incidents/results/export", {
    responseType: "blob",
  });

  return {
    blob: response.data as Blob,
    fileName: extractFileName(response.headers["content-disposition"]),
  };
}
