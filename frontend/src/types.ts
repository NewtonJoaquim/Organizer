export interface UploadResponse {
  file_id: string;
  original_filename: string;
  sanitized_filename: string;
  size_bytes: number;
  content_type: string;
  extension: string;
  created_at: string;
  message: string;
}

export interface HeaderDetectionResult {
  file_id: string;
  sheet_name: string;
  header_row_index: number;
  confidence_score: number;
  raw_columns: string[];
  sanitized_columns: string[];
  sample_rows: any[][];
  explanation: string;
}

export interface WorkbookInspectionResult {
  file_id: string;
  total_sheets: number;
  sheet_names: string[];
  sheets: HeaderDetectionResult[];
}

export interface ColumnMappingItem {
  original_column: string;
  canonical_column: string;
  confidence?: number;
  confidence_score?: number;
  detected_type?: string;
  transformation_type?: string;
  semantic_reasoning?: string;
}

export interface MappingProposal {
  domain_detected: string;
  mappings?: ColumnMappingItem[];
  sheet_mappings?: Record<string, ColumnMappingItem[] | Record<string, string>>;
  unified_canonical_columns?: string[];
  sort_spec?: SortSpec;
  unmapped_columns?: string[];
  overall_confidence?: number;
  requires_human_review?: boolean;
  explanation?: string;
}

export interface SortCriterion {
  column?: string;
  direction?: 'ASC' | 'DESC';
  indicator_columns?: string[];
  custom_order?: string[];
}

export interface SortSpec {
  criteria: SortCriterion[];
  explanation: string;
  raw_instruction?: string;
}

export interface SemanticOrchestratorResponse {
  proposal: MappingProposal;
  sort_spec?: SortSpec;
  tokens_consumed?: number;
  metadata_only_compliance: boolean;
}

export interface IntegrityAudit {
  pre_process_row_count: number;
  post_process_row_count: number;
  rows_match: boolean;
  pre_process_hash: string;
  post_process_hash: string;
  integrity_verified: boolean;
}

export interface ProcessSpreadsheetResponse {
  file_id: string;
  processed_file_id: string;
  filename: string;
  download_url: string;
  rows_processed: number;
  columns: string[];
  integrity_audit: IntegrityAudit;
  processing_time_ms: number;
  message: string;
}

export interface ConsolidateSheetsResponse {
  file_id: string;
  processed_file_id: string;
  filename: string;
  download_url: string;
  sheets_consolidated: string[];
  rows_per_sheet: Record<string, number>;
  total_rows_consolidated: number;
  columns: string[];
  integrity_audit: {
    total_pre_process_row_count: number;
    total_post_process_row_count: number;
    rows_match: boolean;
    integrity_verified: boolean;
    per_sheet_audit: Record<string, {
      sheet_name: string;
      pre_process_row_count: number;
      post_process_row_count: number;
      integrity_verified: boolean;
    }>;
  };
  processing_time_ms: number;
  message: string;
}
