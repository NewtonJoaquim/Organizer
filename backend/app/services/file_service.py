import shutil
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path
from fastapi import HTTPException, UploadFile, status

from app.core.config import settings
from app.core.security import (
    sanitize_filename,
    validate_file_extension,
    validate_magic_bytes,
)
from app.schemas.upload import UploadResponse

CHUNK_SIZE = 64 * 1024  # 64 KB por chunk


class FileService:
    def __init__(self, temp_dir: Path | None = None) -> None:
        self.temp_dir = temp_dir or settings.TEMP_STORAGE_DIR
        self._ensure_temp_dir()

    def _ensure_temp_dir(self) -> None:
        self.temp_dir.mkdir(parents=True, exist_ok=True)

    async def save_upload_file(self, file: UploadFile) -> UploadResponse:
        """
        Recebe um UploadFile, valida extensão, sanitiza o nome, verifica magic bytes
        e salva de forma segura aplicando streaming com limite estrito de tamanho (20 MB).
        """
        raw_filename = file.filename or "planilha.xlsx"
        ext = validate_file_extension(raw_filename)
        safe_filename = sanitize_filename(raw_filename)

        file_id = str(uuid.uuid4())
        target_dir = self.temp_dir / file_id
        target_dir.mkdir(parents=True, exist_ok=True)
        file_path = target_dir / safe_filename

        total_bytes = 0
        first_chunk = True

        try:
            with open(file_path, "wb") as out_file:
                while chunk := await file.read(CHUNK_SIZE):
                    total_bytes += len(chunk)

                    # Validação de tamanho máximo (RF-01: máximo 20 MB)
                    if total_bytes > settings.MAX_UPLOAD_SIZE_BYTES:
                        raise HTTPException(
                            status_code=status.HTTP_413_CONTENT_TOO_LARGE,
                            detail=(
                                f"Arquivo excede o limite máximo permitido de "
                                f"{settings.MAX_UPLOAD_SIZE_BYTES // (1024 * 1024)} MB."
                            ),
                        )

                    # Validação de integridade nos primeiros bytes (Magic Bytes)
                    if first_chunk:
                        validate_magic_bytes(chunk[:16], ext)
                        first_chunk = False

                    out_file.write(chunk)

            # Caso o arquivo esteja completamente vazio
            if total_bytes == 0:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Arquivo de upload está vazio (0 bytes).",
                )

        except Exception:
            # Em caso de erro ou limite estourado, destrói resíduos imediatamente (Zero Data Retention)
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
            raise

        return UploadResponse(
            file_id=file_id,
            original_filename=raw_filename,
            sanitized_filename=safe_filename,
            size_bytes=total_bytes,
            content_type=file.content_type or "application/octet-stream",
            extension=ext,
            created_at=datetime.now(timezone.utc),
            message="Planilha recebida e validada com integridade de bytes.",
        )

    def get_file_path(self, file_id: str, filename: str | None = None) -> Path:
        """
        Retorna o caminho do arquivo temporário isolado, validando que não ocorra escape do diretório.
        """
        target_dir = (self.temp_dir / file_id).resolve()
        if not target_dir.exists() or not target_dir.is_relative_to(self.temp_dir.resolve()):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Arquivo com ID '{file_id}' não encontrado.",
            )

        if filename:
            file_path = (target_dir / sanitize_filename(filename)).resolve()
            if not file_path.exists() or not file_path.is_relative_to(target_dir):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail=f"Arquivo '{filename}' não encontrado para o ID '{file_id}'.",
                )
            return file_path

        # Se filename não foi especificado, retorna o primeiro arquivo presente na pasta
        files = list(target_dir.glob("*"))
        if not files:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Nenhum arquivo encontrado no diretório do ID '{file_id}'.",
            )
        return files[0]

    def cleanup_file(self, file_id: str) -> bool:
        """
        Remove imediatamente o diretório temporário e os arquivos do file_id (LGPD / Zero Retention).
        """
        target_dir = (self.temp_dir / file_id).resolve()
        if target_dir.exists() and target_dir.is_relative_to(self.temp_dir.resolve()):
            shutil.rmtree(target_dir, ignore_errors=True)
            return True
        return False

    def purge_expired_files(self, ttl_minutes: int | None = None) -> int:
        """
        Remove arquivos temporários que ultrapassaram o tempo limite de vida (RN-04: TTL 15 minutos).
        """
        ttl_seconds = (ttl_minutes or settings.TEMP_FILE_TTL_MINUTES) * 60
        now = time.time()
        purged = 0

        if not self.temp_dir.exists():
            return 0

        for item in self.temp_dir.iterdir():
            if item.is_dir():
                mtime = item.stat().st_mtime
                if (now - mtime) > ttl_seconds:
                    shutil.rmtree(item, ignore_errors=True)
                    purged += 1

        return purged


file_service = FileService()
