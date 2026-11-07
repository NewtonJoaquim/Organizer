from fastapi import APIRouter, status
from app.schemas.header import HeaderDetectionResult, InspectHeadersRequest
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
