from datetime import datetime
from pydantic import BaseModel, Field


class UploadResponse(BaseModel):
    file_id: str = Field(..., description="Identificador único (UUID) do arquivo no armazenamento temporário")
    original_filename: str = Field(..., description="Nome original informado no upload")
    sanitized_filename: str = Field(..., description="Nome seguro sanitizado contra path traversal")
    size_bytes: int = Field(..., description="Tamanho do arquivo em bytes")
    content_type: str = Field(..., description="MIME type detectado ou informado")
    extension: str = Field(..., description="Extensão validada (.xlsx ou .xls)")
    created_at: datetime = Field(..., description="Timestamp de recebimento")
    message: str = Field(default="Arquivo recebido e validado com sucesso")


class CleanupResponse(BaseModel):
    file_id: str
    deleted: bool
    message: str
