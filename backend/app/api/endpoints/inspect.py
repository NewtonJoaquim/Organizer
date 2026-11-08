from fastapi import APIRouter, status
from app.schemas.header import (
    HeaderDetectionResult,
    InspectHeadersRequest,
    WorkbookInspectionRequest,
    WorkbookInspectionResult,
)
from app.services.file_service import file_service
from app.services.header_detector import header_detector

router = APIRouter(prefix="/inspect", tags=["Inspeção e Heurística de Cabeçalhos"])


@router.post(
    "/headers",
    response_model=HeaderDetectionResult,
    status_code=status.HTTP_200_OK,
    summary="Identificação heurística automatizada de cabeçalhos (RF-02)",
    description=(
        "Inspeciona as primeiras 15 linhas do arquivo indicado por file_id, "
        "calculando scores de densidade, textualidade, unicidade e continuidade. "
        "Descarta ruídos/preâmbulos institucionais e retorna a linha identificada "
        "e os nomes das colunas."
    ),
)
async def inspect_headers(request: InspectHeadersRequest) -> HeaderDetectionResult:
    file_path = file_service.get_file_path(request.file_id)
    return header_detector.detect_header(file_path, sheet_name=request.sheet_name)


@router.post(
    "/workbook",
    response_model=WorkbookInspectionResult,
    status_code=status.HTTP_200_OK,
    summary="Inspeção heurística de todas as abas da pasta de trabalho (RF-06)",
    description=(
        "Inspeciona automaticamente todas as abas presentes na pasta de trabalho .xlsx ou .xls, "
        "detectando os cabeçalhos, pontuação de confiança e colunas de cada uma individualmente."
    ),
)
async def inspect_workbook(request: WorkbookInspectionRequest) -> WorkbookInspectionResult:
    file_path = file_service.get_file_path(request.file_id)
    return header_detector.inspect_workbook(file_path, file_id=request.file_id)

