import {
  UploadResponse,
  WorkbookInspectionResult,
  HeaderDetectionResult,
  SemanticOrchestratorResponse,
  ProcessSpreadsheetResponse,
  ConsolidateSheetsResponse,
} from './types'

const BASE_URL = '/api'

export async function uploadFile(file: File): Promise<UploadResponse> {
  const formData = new FormData()
  formData.append('file', file)

  const response = await fetch(`${BASE_URL}/upload`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || `Falha no upload (Status ${response.status})`)
  }

  return response.json()
}

export async function inspectWorkbook(fileId: string): Promise<WorkbookInspectionResult> {
  const response = await fetch(`${BASE_URL}/inspect/workbook`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id: fileId }),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || 'Falha ao inspecionar abas da pasta de trabalho')
  }

  return response.json()
}

export async function inspectHeaders(fileId: string, sheetName?: string): Promise<HeaderDetectionResult> {
  const response = await fetch(`${BASE_URL}/inspect/headers`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ file_id: fileId, sheet_name: sheetName }),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || 'Falha ao detectar cabeçalhos da planilha')
  }

  return response.json()
}

export async function semanticMap(
  columns: string[],
  userInstruction: string,
  domainHint?: string
): Promise<SemanticOrchestratorResponse> {
  const response = await fetch(`${BASE_URL}/semantic/map`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      columns,
      user_instruction: userInstruction,
      domain_hint: domainHint,
    }),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || 'Falha na inferência semântica de mapeamento')
  }

  return response.json()
}

export async function semanticMapMultiSheet(
  sheets: Record<string, string[]>,
  userInstruction: string,
  domainHint?: string
): Promise<any> {
  const response = await fetch(`${BASE_URL}/semantic/map-multi-sheet`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      sheets,
      user_instruction: userInstruction,
      domain_hint: domainHint,
    }),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || 'Falha no mapeamento semântico multi-abas')
  }

  return response.json()
}

export async function processSpreadsheet(payload: any): Promise<ProcessSpreadsheetResponse> {
  const response = await fetch(`${BASE_URL}/process`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || 'Falha no processamento determinístico')
  }

  return response.json()
}

export async function consolidateSheets(payload: any): Promise<ConsolidateSheetsResponse> {
  const response = await fetch(`${BASE_URL}/process/consolidate`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })

  if (!response.ok) {
    const errorData = await response.json().catch(() => ({}))
    throw new Error(errorData.detail || 'Falha na consolidação de múltiplas abas')
  }

  return response.json()
}
