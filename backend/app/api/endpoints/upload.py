from fastapi import APIRouter, File, HTTPException, UploadFile, status
from app.schemas.upload import CleanupResponse, UploadResponse
from app.services.file_service import file_service

router = APIRouter(prefix="/upload", tags=["Ingestão de Planilhas"])


@router.post(
    "",
    response_model=UploadResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Upload multipart de planilhas (.xlsx e .xls)",
    description=(
        "Recebe uma planilha nos formatos Microsoft Excel (.xlsx ou .xls) de até 20 MB, "
        "valida integridade de bytes, sanitiza o nome contra path traversal e armazena em "
        "diretório isolado para posterior processamento."
    ),
)
async def upload_spreadsheet(
    file: UploadFile = File(..., description="Arquivo de planilha (.xlsx ou .xls)"),
) -> UploadResponse:
    return await file_service.save_upload_file(file)


@router.delete(
    "/{file_id}",
    response_model=CleanupResponse,
    summary="Descarte imediato de arquivo temporário",
    description="Exclui o arquivo e pasta temporária associados ao ID (LGPD / Zero Data Retention).",
)
async def cleanup_uploaded_file(file_id: str) -> CleanupResponse:
    deleted = file_service.cleanup_file(file_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Arquivo com ID '{file_id}' não localizado para descarte.",
        )
    return CleanupResponse(
        file_id=file_id,
        deleted=True,
        message="Arquivo temporário descartado com sucesso.",
    )
