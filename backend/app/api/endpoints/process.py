from pathlib import Path
from typing import Any
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse
from starlette.background import BackgroundTask

from app.core.config import settings
from app.schemas.process import (
    ConsolidateSheetsRequest,
    ConsolidateSheetsResponse,
    ProcessSpreadsheetRequest,
    ProcessSpreadsheetResponse,
)
from app.services.file_service import file_service
from app.services.processor import deterministic_engine

router = APIRouter(prefix="/process", tags=["Processamento Determinístico e Ordenação Local"])


@router.post(
    "",
    response_model=ProcessSpreadsheetResponse,
    status_code=status.HTTP_200_OK,
    summary="Processamento determinístico e ordenação algorítmica local (RF-05)",
    description=(
        "Executa a leitura tabular determinística, corte de ruídos de cabeçalho, ordenação estável "
        "via mergesort em Pandas e geração do arquivo .xlsx limpo e estilizado para download. "
        "Realiza auditoria matemática estrita com hash multiset (RNF-02) comprovando zero alucinação."
    ),
)
async def process_spreadsheet(request: ProcessSpreadsheetRequest) -> ProcessSpreadsheetResponse:
    return deterministic_engine.process(request)


@router.post(
    "/consolidate",
    response_model=ConsolidateSheetsResponse,
    status_code=status.HTTP_200_OK,
    summary="Consolidação e merge determinístico de múltiplas abas heterogêneas (RF-06)",
    description=(
        "Identifica e lê todas as abas (ou subconjunto especificado) de uma pasta de trabalho .xlsx ou .xls. "
        "Aplica o mapeamento semântico canônico individualmente em cada aba, concatena verticalmente "
        "as linhas alinhando colunas sem duplicação de schema, insere a coluna identificadora da aba de origem "
        "e audita a integridade matemática estrita (RNF-02)."
    ),
)
async def consolidate_sheets(request: ConsolidateSheetsRequest) -> ConsolidateSheetsResponse:
    return deterministic_engine.consolidate(request)



@router.get(
    "/download/{processed_file_id}",
    response_class=FileResponse,
    summary="Download do arquivo processado (.xlsx)",
    description=(
        "Permite baixar a planilha higienizada e ordenada gerada pelo motor determinístico. "
        "Expurga imediatamente os resíduos em disco após o término do streaming (RN-04 e RNF-03)."
    ),
)
async def download_processed_spreadsheet(processed_file_id: str) -> FileResponse:
    target_dir = settings.TEMP_STORAGE_DIR / processed_file_id
    if not target_dir.exists():
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arquivo processado com ID '{processed_file_id}' não encontrado ou expirado.",
        )

    files = list(target_dir.glob("*.xlsx"))
    if not files:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Nenhuma planilha formatada encontrada no diretório informado.",
        )

    file_path = files[0]

    # Agenda a destruição imediata de arquivos após a conclusão da transmissão HTTP (DoD TSK-S1-05)
    cleanup_task = BackgroundTask(file_service.cleanup_workflow, processed_file_id)

    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=file_path.name,
        background=cleanup_task,
    )


@router.get(
    "/audit/storage",
    summary="Auditoria de conformidade de armazenamento (Zero Data Retention / LGPD)",
    description="Retorna a contagem de diretórios temporários em disco e status de conformidade LGPD.",
)
async def audit_storage() -> dict[str, Any]:
    active_count = file_service.count_active_directories()
    return {
        "active_temp_directories": active_count,
        "zero_retention_compliant": active_count == 0,
        "ttl_minutes": settings.TEMP_FILE_TTL_MINUTES,
    }
