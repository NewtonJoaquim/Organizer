from pathlib import Path
from fastapi import APIRouter, HTTPException, status
from fastapi.responses import FileResponse

from app.core.config import settings
from app.schemas.process import (
    ProcessSpreadsheetRequest,
    ProcessSpreadsheetResponse,
)
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


@router.get(
    "/download/{processed_file_id}",
    response_class=FileResponse,
    summary="Download do arquivo processado (.xlsx)",
    description="Permite baixar a planilha higienizada e ordenada gerada pelo motor determinístico.",
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
    return FileResponse(
        path=file_path,
        media_type="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
        filename=file_path.name,
    )
