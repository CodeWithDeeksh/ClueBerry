import axios from "axios";

const api = axios.create({ baseURL: "" });

export interface DocumentMeta {
  document_id: string;
  filename: string;
  s3_key: string;
  document_type: string;
  status: "UPLOADED" | "PROCESSING" | "READY" | "FAILED";
  upload_timestamp: string;
  extracted_fields?: Record<string, unknown>;
  error?: string;
}

export interface Investigation {
  investigation_id: string;
  question: string;
  document_ids: string[];
  status: "queued" | "running" | "complete" | "failed";
  mcp_tool_calls: MCPToolCall[];
  report?: InvestigationReport;
  created_at: string;
  completed_at?: string;
  error?: string;
}

export interface MCPToolCall {
  tool_name: string;
  parameters: Record<string, unknown>;
  result_summary: string;
  evidence_ids: string[];
  timestamp: string;
}

export interface TimelineEntry {
  date?: string;
  event: string;
  document_id: string;
  source_filename: string;
  evidence_id?: string;
}

export interface InvestigationReport {
  finding: string;
  summary: string;
  match_status: string;
  evidence_list: Array<{
    evidence_id: string;
    document_id: string;
    source_filename: string;
    field: string;
    value: string;
  }>;
  contradictions: string[];
  timeline: TimelineEntry[];
  confidence_note: string;
  draft_response: string;
}

// Documents
export const uploadDocument = async (file: File): Promise<{ document_id: string; filename: string; status: string }> => {
  const form = new FormData();
  form.append("file", file);
  const res = await api.post("/documents/upload", form);
  return res.data;
};

export const listDocuments = async (): Promise<DocumentMeta[]> => {
  const res = await api.get("/documents");
  return res.data;
};

export const getDocument = async (id: string): Promise<DocumentMeta> => {
  const res = await api.get(`/documents/${id}`);
  return res.data;
};

// Investigations
export const startInvestigation = async (question: string, documentIds: string[]): Promise<{ investigation_id: string; status: string }> => {
  const res = await api.post("/investigations", { question, document_ids: documentIds });
  return res.data;
};

export const getInvestigation = async (id: string): Promise<Investigation> => {
  const res = await api.get(`/investigations/${id}`);
  return res.data;
};

export const getReport = async (id: string): Promise<InvestigationReport> => {
  const res = await api.get(`/investigations/${id}/report`);
  return res.data;
};

export const checkHealth = async (): Promise<{ status: string }> => {
  const res = await api.get("/health");
  return res.data;
};
