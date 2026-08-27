export interface IncidentAnalysisResult {
  total_processed: number;
  valid_records: number;
  invalid_records: number;
  validation_errors: Record<string, number>;
  validation_errors_raw: Record<string, number>;
  validation_error_details: string[];
  by_category: Record<string, number>;
  by_status: Record<string, number>;
  average_satisfaction: number | null;
}

export interface ExportedResult {
  fileName: string;
  blob: Blob;
}
